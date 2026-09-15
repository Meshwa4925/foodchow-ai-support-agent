import os
import json
import faiss

from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

VECTOR_STORE_DIR = os.path.join(
    BASE_DIR,
    "rag",
    "vector_store"
)

INDEX_FILE = os.path.join(
    VECTOR_STORE_DIR,
    "knowledge_base.index"
)

DOCUMENTS_FILE = os.path.join(
    VECTOR_STORE_DIR,
    "documents.json"
)


# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# --------------------------------------------------
# LOAD FAISS INDEX
# --------------------------------------------------

if not os.path.exists(INDEX_FILE):
    raise FileNotFoundError(
        "FAISS index not found. "
        "Please run create_embeddings.py first."
    )

index = faiss.read_index(
    INDEX_FILE
)


# --------------------------------------------------
# LOAD DOCUMENTS
# --------------------------------------------------

if not os.path.exists(DOCUMENTS_FILE):
    raise FileNotFoundError(
        "documents.json not found. "
        "Please run create_embeddings.py first."
    )

with open(
    DOCUMENTS_FILE,
    "r",
    encoding="utf-8"
) as file:

    documents = json.load(file)


# --------------------------------------------------
# SEARCH FUNCTION
# --------------------------------------------------

def search_knowledge_base(
    query,
    top_k=3
):

    # Create embedding for customer query
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True
    )

    # Search FAISS
    distances, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for distance, index_number in zip(
        distances[0],
        indices[0]
    ):

        if index_number < 0:
            continue

        document = documents[index_number]

        results.append(
            {
                "source": document["source"],
                "content": document["content"],
                "distance": float(distance)
            }
        )

    return results


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    print("--------------------------------")
    print("FoodChow RAG Search Test")
    print("--------------------------------")

    query = input(
        "\nEnter customer issue: "
    )

    results = search_knowledge_base(
        query,
        top_k=3
    )

    print("\nRelevant Knowledge:\n")

    for i, result in enumerate(
        results,
        start=1
    ):

        print("=" * 60)

        print(
            f"Result {i}"
        )

        print(
            f"Source: {result['source']}"
        )

        print(
            f"Distance: {result['distance']:.4f}"
        )

        print("\nContent:")

        print(
            result["content"]
        )

    print("=" * 60)