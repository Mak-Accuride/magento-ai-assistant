from src.rag.rag_chain import build_rag_chain
from src.rag.formatter import format_rag_response

qa = build_rag_chain()
raw = qa.invoke({"input": "Is there a freezer around 550 liters?"})
print(format_rag_response(raw))
