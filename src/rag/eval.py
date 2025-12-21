from src.rag.formatter import format_rag_response
from src.rag.rag_chain import build_rag_chain
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
TEST_QUERIES = {
    "A":"kitchen drawers",
    "B":"large pocket door system",
    "C":"energy efficient freezer",
    "D":"does this include warranty?",
    "E":"how to cook pasta"
}


def run_eval():
    qa = build_rag_chain()

    for key, query in TEST_QUERIES.items():
        print("=" * 60)
        print(f"Q {key}: {query}")
        
        # Invoke with correct dict format
        res = qa.invoke({"input": query})
        
        print(format_rag_response(res))
        print("\n")


if __name__ == "__main__":
    run_eval()
