import random
from langchain.chat_models import init_chat_model

if random.random() < 0.5:
    print("gpt-4.1-mini selected")
    model = init_chat_model("gpt-4.1-mini")
else:
    print("claude-3-5-sonnet-latest selected")
    model = init_chat_model("claude-3-5-sonnet-latest", model_provider="anthropic")
result = model.invoke("RAG가 뭔가요?")
print(result.content)
