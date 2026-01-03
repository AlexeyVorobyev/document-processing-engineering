import traceback

from src.common.dependency_injection.injectable import injectable
from src.common.interfaces.runnable import IRunnable
from src.common.logger.logger_mixin import LoggerMixin
from src.kdctl.argument_parser import ApplicationArgumentParser
from src.kdctl.commands.commands_mapping import (
    CommandsFactoryMapping,
)


@injectable(container_tags=["KDCTL"])
class Application(LoggerMixin, IRunnable):
    __commands_mapping: CommandsFactoryMapping
    __parser: ApplicationArgumentParser

    def __init__(
        self,
        commands_mapping: CommandsFactoryMapping,
        parser: ApplicationArgumentParser,
    ) -> None:
        self.__commands_mapping = commands_mapping
        self.__parser = parser

    async def run(self) -> None:
        namespace = self.__parser.parse_args()
        command = self.__commands_mapping[namespace.command]()
        try:
            await command.execute(namespace)
        except Exception as error:
            self._logger.error(
                f"Captured error {traceback.format_exception_only(error)}: {error}"
            )
