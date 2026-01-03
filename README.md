# Платформа обработки документации Terraform-провайдеров

Этот сервис выполняет фоновую обработку документации провайдеров Terraform и загрузку готовых векторных данных в Qdrant. Поток задач запускается в асинхронном воркере и проходит через набор узлов пайплайна.

## Архитектура запуска
- **Точка входа:** `src/documentation_processing/main.py` создаёт контейнер зависимостей и запускает `Application.run()`.
- **Инициализация:** приложение поднимает подключение к MongoDB и стартует набор воркеров (`Workers`), после чего работает в вечном цикле.
- **Воркеры:** `DocumentationProcessingWorker` наследуется от `BaseAsyncioWorker`, выполняет пайплайн обработки и затем спит сутки (`_worker_interval` = 1 день) перед следующим запуском.

## Этапы пайплайна
1. **Загрузка настроек провайдеров** (`LoadProviderSettingsNode`)
   - Читает коллекцию `provider_settings` в MongoDB (модель `ProviderSettings`).
   - Отбирает только записи с `enabled = true` и формирует список провайдеров `namespace/name` для обработки.

2. **Выбор версий для обработки** (`ProviderVersionSelectionNode`)
   - Для каждого провайдера запрашивает Terraform Registry (`/v2/providers/{namespace}/{name}?include=provider-versions`).
   - Находит самую свежую версию по полю публикации и пропускает, если такая версия уже есть в коллекции `provider_versions` (`ProviderVersionDocument`).
   - Сохраняет список новых версий (`versions_to_process`) для последующего шага.

3. **Обработка выбранных версий** (`ProcessProviderVersionNode`)
   - Создаёт рабочий каталог `src/workspace/documentation_processing/<run_id>/` с подпапками:
     - `raw_documents` — индивидуальные страницы провайдера, загруженные из Registry (`/v2/provider-docs/{id}`).
     - `raw_documents_combined` — объединённый Markdown по провайдеру/версии.
     - `prepared` — результаты очистки и разметки документов.
     - `vectorized` — эмбеддинги, готовые к загрузке в векторное хранилище.
   - Для каждой версии:
     1. Получает идентификаторы страниц документации (`include=provider-docs` для `/v2/provider-versions/{id}`).
     2. Скачивает контент каждой страницы в `raw_documents` и объединяет в единый Markdown.
     3. Запускает CLI `kdctl documents-prepare` с метаданными провайдера/версии, что очищает текст и складывает результат в `prepared/<provider>_<version>/`.
     4. Запускает `kdctl documents-vectorize`, генерируя эмбеддинги в `vectorized/<provider>_<version>/`.
     5. Загружает эмбеддинги в Qdrant через `kdctl documents-upload` с параметрами подключения из настроек (`DPB_DB_QDRANT_*`, коллекция из `app.vector_database_collection`).
     6. Фиксирует успешную обработку в MongoDB (`ProviderVersionDocument`), чтобы пропускать ту же версию при следующих запусках.

## Настройки
- Используются переменные окружения с префиксом `DPB_` (см. `settings.py`).
- Ключевые параметры:
  - MongoDB (`DPB_DB_MONGO__*`) — доступ к коллекциям настроек и истории обработанных версий.
  - Qdrant (`DPB_DB_QDRANT__*`) — адрес, порт, пароль и признак защищённого подключения.
  - OpenAI (`DPB_APP__OPENAI_API_KEY`, `DPB_APP__MODEL_NAME`, опционально `DPB_APP__LLM_BASE_URL`) — используются `kdctl documents-prepare`/`documents-vectorize`.
  - Общие (`DPB_APP__VECTOR_DATABASE_COLLECTION`, `DPB_APP__LOG_LEVEL`) — имя коллекции в Qdrant и уровень логирования.

## Основные зависимости и процессы
- **Beanie/MongoDB** — хранит перечень провайдеров к обработке (`provider_settings`) и уже обработанные версии (`provider_versions`).
- **aiohttp** — HTTP-клиент для вызовов Terraform Registry и загрузки Markdown страниц.
- **kdctl CLI** (`src.kdctl.main`) — утилита подготовки, векторизации и загрузки данных в Qdrant; запускается через отдельные процессы.
- **Workspace артефакты** — результаты каждой сессии складываются в `src/workspace/documentation_processing/<run_id>/` и могут использоваться для отладки качества данных.

