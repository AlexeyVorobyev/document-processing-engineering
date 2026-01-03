import asyncio

from src.common.dependency_injection.register_modules import (
    register_modules,
)
from src.kdctl.di import DependencyInjector


async def main() -> None:
    dependency_injector = DependencyInjector()

    dependency_injector.wire(
        packages=[
            "src.kdctl",
        ],
    )

    app = dependency_injector.application()

    del dependency_injector

    await app.run()


if __name__ == "__main__":
    register_modules("src.kdctl", DependencyInjector)
    asyncio.run(main())
