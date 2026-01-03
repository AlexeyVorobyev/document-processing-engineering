from argparse import ArgumentParser, Namespace

from src.common.dependency_injection.injectable import (
    injectable,
)
from src.kdctl.commands.commands_mapping import CommandName


@injectable(container_tags=["KDCTL"])
class ApplicationArgumentParser:
    __parser: ArgumentParser

    def __init__(self) -> None:
        self.__parser = ArgumentParser("Knowledge database controller.")
        self.__prepare_commands_parsers()

    def parse_args(self) -> Namespace:
        return self.__parser.parse_args()

    def __prepare_commands_parsers(self) -> None:
        subparsers = self.__parser.add_subparsers(help="Available commands")
        self.__prepare_documents_upload_command_parser(
            subparsers.add_parser(
                name=CommandName.DOCUMENTS_UPLOAD,
                help="Prepare and upload documents to database.",
            )
        )
        self.__prepare_documents_download_command_parser(
            subparsers.add_parser(
                name=CommandName.DOCUMENTS_DOWNLOAD,
                help="Download documents from database.",
            )
        )
        self.__prepare_documents_prepare_command_parser(
            subparsers.add_parser(
                name=CommandName.DOCUMENTS_PREPARE,
                help="Prepare documents from raw file.",
            )
        )
        self.__prepare_documents_vectorize_command_parser(
            subparsers.add_parser(
                name=CommandName.DOCUMENTS_VECTORIZE,
                help="Vectorize documents.",
            )
        )

    def __add_llm_args(self, parser: ArgumentParser, default_model: str) -> None:
        parser.add_argument(
            "--api-key",
            dest="api_key",
            help="API key for LLM",
        )
        parser.add_argument(
            "--base-url",
            dest="base_url",
            default=None,
            help="Base URL for LLM, defaults to null",
        )
        parser.add_argument(
            "--model",
            dest="model",
            default=default_model,
            help="Model of LLM",
        )

    def __add_database_args(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--host",
            dest="host",
            default="127.0.0.1",
            help="Host of database for example '127.0.0.1' or 'db.local'",
        )
        parser.add_argument(
            "--port",
            "-p",
            dest="port",
            type=int,
            default=6333,
            help="Port of database for example '6333'",
        )
        parser.add_argument(
            "--password",
            dest="password",
            required=True,
            help="Password of database",
        )
        parser.add_argument(
            "--secured",
            "-s",
            dest="secured",
            action="store_true",
            default=False,
            help="Is connection to database via https",
        )
        parser.add_argument(
            "--collection",
            dest="collection",
            default="knowledge_collection",
            help="Collection of database",
        )

    def __prepare_documents_upload_command_parser(self, parser: ArgumentParser) -> None:
        parser.set_defaults(command=CommandName.DOCUMENTS_UPLOAD)
        self.__add_database_args(parser)
        parser.add_argument(
            "--input",
            "-i",
            dest="input",
            default=".",
            help="Directory where to collect files, defaults to cwd",
        )

    def __prepare_documents_download_command_parser(
        self, parser: ArgumentParser
    ) -> None:
        parser.set_defaults(command=CommandName.DOCUMENTS_DOWNLOAD)
        self.__add_database_args(parser)
        parser.add_argument(
            "--output",
            "-o",
            dest="output",
            default=".",
            help="Directory where to store downloaded files, defaults to cwd",
        )

    def __prepare_documents_prepare_command_parser(
        self, parser: ArgumentParser
    ) -> None:
        parser.set_defaults(command=CommandName.DOCUMENTS_PREPARE)
        self.__add_llm_args(parser, "gpt-5-nano")
        parser.add_argument(
            "--input",
            "-i",
            dest="input",
            help="input file for chunking and preparation",
        )
        parser.add_argument(
            "--output",
            "-o",
            dest="output",
            default=".",
            help="Directory where to store prepared files, defaults to cwd",
        )
        parser.add_argument(
            "--metadata",
            dest="metadata",
            default="{}",
            help="Document metadata in json format",
        )

    def __prepare_documents_vectorize_command_parser(
        self, parser: ArgumentParser
    ) -> None:
        parser.set_defaults(command=CommandName.DOCUMENTS_VECTORIZE)
        self.__add_llm_args(parser, "text-embedding-3-large")
        parser.add_argument(
            "--input",
            "-i",
            dest="input",
            help="Directory with files for vectorization",
        )
        parser.add_argument(
            "--output",
            "-o",
            dest="output",
            default=".",
            help="Directory where to store prepared files, defaults to cwd",
        )