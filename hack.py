from uuid import UUID
from pydantic import BaseModel
import httpx
from retryhttp._retry import retry


class Payload(BaseModel):
    uuid: UUID
    id: int
    user_id: int
    user_uuid: UUID


class Defaults(BaseModel):
    timeout: int = 3
    backoff: bool = True


defaults1 = {
    "timeout": 5,
    "backoff": True,
}

defaults2 = Defaults().model_dump()


@retry(**defaults1)
def get_example1(x: int) -> Payload:
    response = httpx.get("https://example.com/")
    response.raise_for_status()

    return Payload(**response.json())


x = get_example1(1).user_id


@retry(**defaults2)
def get_example2(x: int) -> Payload:
    response = httpx.get("https://example.com/")
    response.raise_for_status()

    return Payload(**response.json())


x = get_example2(1).user_id
