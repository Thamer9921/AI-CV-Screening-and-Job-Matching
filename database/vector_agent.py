import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

from functools import lru_cache

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from agents.job_agent import get_job_text


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_model():
    """Load the model once per Python process."""
    try:
        return SentenceTransformer(
            MODEL_NAME,
            device="cpu",
            local_files_only=True,
        )
    except OSError as exc:
        raise RuntimeError(
            "The model is not available locally. "
            "Offline mode is enabled; no download was attempted."
        ) from exc


def encode_texts(texts):
    embeddings = get_model().encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return np.ascontiguousarray(embeddings, dtype=np.float32)


def embed_text(text):
    if not text.strip():
        raise ValueError("Cannot encode empty text.")

    return encode_texts([text])[0]


def build_job_index(jobs):
    if not jobs:
        return None, np.empty((0, 0), dtype=np.float32)

    texts = [get_job_text(job) for job in jobs]

    if any(not text.strip() for text in texts):
        raise ValueError("A job has no readable title or description.")

    embeddings = encode_texts(texts)

    # Normalized inner product equals cosine similarity.
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    return index, embeddings


def search_jobs(cv_text, jobs, index, top_k=None):
    if not jobs:
        return []

    if index is None or index.ntotal != len(jobs):
        raise ValueError("The index does not match the job list.")

    if not cv_text.strip():
        raise ValueError("The CV contains no readable text.")

    # Evaluate all jobs by default before applying final ranking.
    k = len(jobs) if top_k is None else min(int(top_k), len(jobs))
    if k <= 0:
        return []

    query = np.ascontiguousarray(
        embed_text(cv_text).reshape(1, -1),
        dtype=np.float32,
    )
    scores, indices = index.search(query, k)

    results = []

    for score, idx in zip(scores[0], indices[0]):
        if 0 <= idx < len(jobs):
            job = dict(jobs[int(idx)])
            job["semantic_similarity"] = float(
                np.clip(score, -1.0, 1.0)
            )
            results.append(job)

    return results