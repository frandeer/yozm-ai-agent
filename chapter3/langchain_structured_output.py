from pydantic import BaseModel, Field


# 1) ------------------------------------------------------------------------
#   Declare the response structure with Pydantic. LangChain will make the
#   model pass these instructions to the LLM and also validate the JSON that
#   comes back.

from langchain.chat_models import init_chat_model

llm = init_chat_model("gpt-4o-mini", model_provider="openai")


class MovieReview(BaseModel):
    """Structured representation of a single movie review."""

    title: str = Field(description="영화 제목")
    rating: float = Field(description="10점 만점 평점 (예: 7.5)")
    review: str = Field(description="한글 리뷰 (3~4문장)")


# 2) ------------------------------------------------------------------------
#   Build a StructuredOutputParser from the schema.


structured_llm = llm.with_structured_output(MovieReview)

result:MovieReview = structured_llm.invoke("영화 '기생충'에 대한 리뷰를 작성해 주세요.")

print(type(result))
print("==========================")
print(result.title)
print(result.rating)
print(result.review)
