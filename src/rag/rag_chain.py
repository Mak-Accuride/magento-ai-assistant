from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

from src.rag.retriever import ProductRetriever

import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def build_rag_chain():
    # Load your FAISS retriever
    retriever = ProductRetriever().get_retriever(top_k=5)

    # LLM
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.2,
        openai_api_key=OPENAI_API_KEY,
    )

    # Custom prompt (use this one!)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", """
You are a Magento product expert.

Use the following product information to answer the question.
If the retrieved information contains relevant product details that answer the question, provide a clear, factual, concise response.
If the retrieved information is not relevant to the question or does not contain the answer, say "I don't know".

Product Information:
{context}

Answer (clear, factual, concise):
"""),
            ("human", "{input}"),
        ]
    )

    # Build the chains
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    return rag_chain

if __name__ == "__main__":
    qa = build_rag_chain()
    query = "Do you have a 550 liter chest freezer slide?"
    result = qa.invoke({"input": query})
    print("Answer:", result["answer"])
    if "context" in result:
        print("\nSources:")
        for doc in result["context"]:
            print(f"- {doc.page_content[:1000]}...")