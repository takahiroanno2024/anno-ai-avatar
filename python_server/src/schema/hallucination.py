from pydantic import BaseModel


class HallucinationRequest(BaseModel):
    """POST /hallucination のRequestのJSON型"""

    text: str


class HallucinationResponse(BaseModel):
    """POST /hallucination のResponseのJSON型"""

    response_text: str
    rag_qa: str
    rag_knowledge: str
    hal_cls: int
    rag_knowledge_meta: dict[str, str | int]
