from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)

        # 🔥 FIX: dùng content thay vì text
        context = "\n".join([r["content"] for r in results])

        prompt = f"""
Context:
{context}

Question:
{question}

Answer:
"""
        return self.llm_fn(prompt)