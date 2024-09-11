from typing import List

from pydantic import BaseModel


class Message(BaseModel):
    content: str
    role: str = "user"


class ChatRequest(BaseModel):
    messages: List[Message]
    stream: bool = True
