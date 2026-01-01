from pydantic import BaseModel


class ConversationalHistoryModel(BaseModel):
    question: str
    answer: str
    timestamp: str
