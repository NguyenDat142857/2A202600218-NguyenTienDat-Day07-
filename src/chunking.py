from __future__ import annotations

import math
import re


class FixedSizeChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        sentences = re.split(r'(?<=[.!?])\s+|\n', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk = " ".join(sentences[i:i + self.max_sentences_per_chunk])
            chunks.append(chunk.strip())

        return chunks


class RecursiveChunker:
    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text.strip()]

        if not remaining_separators:
            return [current_text[: self.chunk_size].strip()]

        sep = remaining_separators[0]

        if sep == "":
            return [
                current_text[i:i + self.chunk_size].strip()
                for i in range(0, len(current_text), self.chunk_size)
            ]

        parts = current_text.split(sep)

        chunks = []
        buffer = ""

        for part in parts:
            if not buffer:
                buffer = part
            elif len(buffer) + len(sep) + len(part) <= self.chunk_size:
                buffer += sep + part
            else:
                chunks.extend(self._split(buffer, remaining_separators[1:]))
                buffer = part

        if buffer:
            chunks.extend(self._split(buffer, remaining_separators[1:]))

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot = _dot(vec_a, vec_b)
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


class ChunkingStrategyComparator:
    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size),
            "by_sentences": SentenceChunker(),   # 🔥 FIX tên key
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        results = {}

        for name, strategy in strategies.items():
            chunks = strategy.chunk(text)

            results[name] = {
                "count": len(chunks),
                "avg_length": sum(len(c) for c in chunks) / len(chunks) if chunks else 0,
                "chunks": chunks   # 🔥 FIX thêm field này
            }

        return results