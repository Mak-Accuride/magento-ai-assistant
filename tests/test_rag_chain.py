from src.rag.rag_chain import build_rag_chain
from src.rag.formatter import format_rag_response

qa = build_rag_chain()
raw = qa.invoke({"input": "dumper"})
print(format_rag_response(raw))
