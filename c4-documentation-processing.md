# C4-диаграмма обработки документации и KDCTL

Диаграмма описывает, как сервис `src/documentation_processing` и CLI `src/kdctl` готовят данные для внешней системы **ai-infra-agent**, которая использует векторную базу для RAG-поиска. Ниже приведены уровни C4: контекст, контейнеры и ключевые компоненты.

## Контекст системы
```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml
LAYOUT_WITH_LEGEND()

Person(agent, "ai-infra-agent", "Использует RAG-поиск по векторной базе")
System_Boundary(dp, "Documentation Processing") {
  System(dp_worker, "documentation_processing", "Асинхронный воркер, который по расписанию запускает пайплайн")
  System(kdctl, "kdctl CLI", "CLI для подготовки, векторизации и загрузки документов")
}
System_Ext(qdrant, "Vector Database (Qdrant)", "Хранит эмбеддинги документации")
System_Ext(mongo, "MongoDB", "Хранит настройки провайдеров и истории версий")
System_Ext(registry, "Terraform Registry", "Источник Markdown документации провайдеров")
System_Ext(openai, "OpenAI API / LLM endpoint", "Создание чистого текста и эмбеддингов")

Rel(agent, qdrant, "Извлекает релевантные фрагменты для ответов")
Rel(dp_worker, registry, "GET /provider-docs, скачивание Markdown")
Rel(dp_worker, mongo, "Читает provider_settings и сохраняет обработанные версии")
Rel(dp_worker, kdctl, "Запускает CLI-команды как подпроцессы")
Rel(kdctl, openai, "Генерирует эмбеддинги и очищенный текст")
Rel(kdctl, qdrant, "Загружает готовые векторы в коллекцию")
@enduml
```

## Диаграмма контейнеров
```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml
LAYOUT_WITH_LEGEND()

Person(agent, "ai-infra-agent")
System_Boundary(system, "Documentation Processing & KDCTL") {
  Container(dp_app, "Application.run()", "Python + aiohttp", "Поднимает DI-контейнер, воркеров и вечный цикл")
  Container(dp_worker, "DocumentationProcessingWorker", "Asyncio worker", "Раз в сутки инициирует пайплайн обработки провайдеров")
  Container(dp_pipeline, "Nodes pipeline", "LangGraph-style nodes", "LoadProviderSettings -> ProviderVersionSelection -> ProcessProviderVersion")
  Container(kdctl_cli, "kdctl main", "Click-like CLI", "Парсит команды documents-* и делегирует исполнение")
  Container(kdctl_commands, "KDCTL commands", "documents-download/prepare/vectorize/upload", "Работают с файлами, OpenAI и Qdrant")
  Container(filesystem, "Workspace артефакты", "filesystem", "raw_documents, prepared, vectorized для каждой сессии")
}
System_Ext(qdrant, "Vector Database (Qdrant)")
System_Ext(mongo, "MongoDB")
System_Ext(registry, "Terraform Registry")
System_Ext(openai, "OpenAI API / Embeddings")

Rel(agent, qdrant, "Vector search / retrieve")
Rel(dp_app, dp_worker, "Создаёт и запускает")
Rel(dp_worker, dp_pipeline, "Оркеструет узлы")
Rel(dp_pipeline, mongo, "Читает настройки и фиксирует версии")
Rel(dp_pipeline, registry, "Скачивает страницы документации")
Rel(dp_pipeline, filesystem, "Сохраняет raw/combined Markdown")
Rel(dp_pipeline, kdctl_cli, "Запускает documents-prepare/vectorize/upload для каждой версии")
Rel(kdctl_cli, kdctl_commands, "Создаёт ICommand по args")
Rel(kdctl_commands, filesystem, "Читает подготовленные файлы, записывает результаты")
Rel(kdctl_commands, openai, "Получает очистку текста и эмбеддинги")
Rel(kdctl_commands, qdrant, "Создаёт коллекции и грузит эмбеддинги")
@enduml
```

## Диаграмма компонентов
```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml
LAYOUT_WITH_LEGEND()

Container_Boundary(dp, "documentation_processing") {
  Component(load_settings, "LoadProviderSettingsNode", "MongoDB reader", "Берёт enabled провайдеров из provider_settings")
  Component(select_versions, "ProviderVersionSelectionNode", "Terraform Registry client", "Находит свежие версии, проверяет provider_versions")
  Component(process_versions, "ProcessProviderVersionNode", "Pipeline orchestrator", "Скачивает страницы, вызывает kdctl, грузит в Qdrant")
  Component(worker, "DocumentationProcessingWorker", "BaseAsyncioWorker", "Запускает узлы и планирует следующий запуск")
}
Container_Boundary(kdctl, "kdctl commands") {
  Component(download, "DocumentsDownloadCommand", "Qdrant scroll", "Выгружает payload+векторы пакетами и сохраняет JSON")
  Component(prepare, "DocumentsPrepareCommand", "LLM cleaner", "Очищает/нормализует Markdown для эмбеддингов")
  Component(vectorize, "DocumentsVectorizeCommand", "Embedding generator", "Генерирует векторы через OpenAI/LLM endpoint")
  Component(upload, "DocumentsUploadCommand", "Qdrant importer", "Создаёт коллекцию и загружает батчами")
}
Container(qdrant, "Vector Database")
Container(mongo, "MongoDB")
Container(registry, "Terraform Registry")
Container(openai, "OpenAI API")
Person(agent, "ai-infra-agent")

Rel(worker, load_settings, "Стартует цикл")
Rel(load_settings, select_versions, "Передаёт список провайдеров")
Rel(select_versions, process_versions, "Формирует версии к обработке")
Rel(process_versions, registry, "GET provider-docs, скачивание страниц")
Rel(process_versions, prepare, "Запускает kdctl documents-prepare")
Rel(process_versions, vectorize, "Запускает kdctl documents-vectorize")
Rel(process_versions, upload, "Запускает kdctl documents-upload")
Rel(process_versions, mongo, "Фиксирует обработанные версии")
Rel(download, qdrant, "Scroll + сохранение в файловую систему")
Rel(prepare, openai, "LLM очистка/структурирование")
Rel(vectorize, openai, "Создание эмбеддингов")
Rel(upload, qdrant, "Upsert/collection management")
Rel(agent, qdrant, "Читает векторные документы для RAG")
@enduml
```

Диаграммы показывают, как `documentation_processing` использует `kdctl` для загрузки и подготовки данных, а внешняя система **ai-infra-agent** читает готовые векторные документы из Qdrant.
