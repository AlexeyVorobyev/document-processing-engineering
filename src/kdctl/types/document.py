from typing import Any, TypedDict

type Vector = list[Any]


class DocumentPayload(TypedDict):
    page_content: str
    metadata: dict[str, Any]


class Document(TypedDict):
    id: str
    payload: DocumentPayload
    vector: Vector | None
