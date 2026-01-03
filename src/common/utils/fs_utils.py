import asyncio
import json
from pathlib import Path
from typing import cast

import aiofiles

from src.ai_agent_infrastructure.components.types.types import JsonSerializable


def load_data_from_file_sync(file_path: Path) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        return content


def load_json_from_file_sync(file_path: Path) -> JsonSerializable:
    content = load_data_from_file_sync(file_path)
    return cast(JsonSerializable, json.loads(content))


def save_json_to_file_sync(file_path: Path, content: JsonSerializable) -> None:
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(json.dumps(content))


def check_path_sync(path: Path) -> None:
    is_exist = path.exists()

    if not is_exist:
        raise RuntimeError(f"Path {path} does not exist")


async def load_data_from_file(file_path: Path) -> str:
    async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
        return await file.read()


async def load_json_from_file(file_path: Path) -> JsonSerializable:
    content = await load_data_from_file(file_path)
    return cast(JsonSerializable, json.loads(content))


async def save_data_to_file(file_path: Path, content: str) -> None:
    async with aiofiles.open(file_path, "w", encoding="utf-8") as file:
        await file.truncate(0)
        await file.write(content)


async def save_json_to_file(file_path: Path, content: JsonSerializable) -> None:
    json_content = json.dumps(content)
    await save_data_to_file(file_path, json_content)


async def create_file(file_path: Path) -> None:
    await save_data_to_file(file_path, "")


async def check_path(path: Path) -> None:
    is_exist = await asyncio.to_thread(path.exists)

    if not is_exist:
        raise RuntimeError(f"Path {path} does not exist")
