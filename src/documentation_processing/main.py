import asyncio

from src.documentation_processing.dependency_injector import DependencyInjector
from src.common.dependency_injection.register_modules import register_modules


async def main() -> None:
    dependency_injector = DependencyInjector()

    dependency_injector.wire(
        packages=["src.documentation_processing"],
    )

    app = dependency_injector.application()

    del dependency_injector

    await app.run()


if __name__ == "__main__":
    register_modules("src.documentation_processing", DependencyInjector)
    asyncio.run(main())
