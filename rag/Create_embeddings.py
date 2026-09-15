import os
import json
import faiss

from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

KNOWLEDGE_BASE_DIR = os.path.join(
    BASE_DIR,
    "knowledge_base"
)

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
# CREATE VECTOR STORE DIRECTORY
# --------------------------------------------------

os.makedirs(VECTOR_STORE_DIR, exist_ok=True)


# --------------------------------------------------
# LOAD EMBEDDING MODEL
# --------------------------------------------------

print("Loading embedding model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Embedding model loaded.")


# --------------------------------------------------
# READ KNOWLEDGE BASE FILES
# --------------------------------------------------

documents = []

for filename in os.listdir(KNOWLEDGE_BASE_DIR):

    if filename.endswith(".md"):

        file_path = os.path.join(
            KNOWLEDGE_BASE_DIR,
            filename
        )

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            content = file.read()

        documents.append(
            {
                "source": filename,
                "content": content
            }
        )

        print(
            f"Loaded knowledge file: {filename}"
        )


# --------------------------------------------------
# CHECK DOCUMENTS
# --------------------------------------------------

if not documents:

    print("No knowledge base files found.")

    raise SystemExit


# --------------------------------------------------
# CREATE TEXT LIST
# --------------------------------------------------

texts = [
    document["content"]
    for document in documents
]


# --------------------------------------------------
# CREATE EMBEDDINGS
# --------------------------------------------------

print("\nCreating embeddings...")

embeddings = model.encode(
    texts,
    convert_to_numpy=True
)

print("Embeddings created.")


# --------------------------------------------------
# CREATE FAISS INDEX
# --------------------------------------------------

dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(
    dimension
)

index.add(embeddings)


# --------------------------------------------------
# SAVE FAISS INDEX
# --------------------------------------------------

faiss.write_index(
    index,
    INDEX_FILE
)


# --------------------------------------------------
# SAVE DOCUMENT INFORMATION
# --------------------------------------------------

with open(
    DOCUMENTS_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        documents,
        file,
        indent=4,
        ensure_ascii=False
    )


# --------------------------------------------------
# SUCCESS MESSAGE
# --------------------------------------------------

print("\n--------------------------------")
print("RAG VECTOR STORE CREATED")
print("--------------------------------")

print(
    f"Documents indexed: {len(documents)}"
)

print(
    f"Vector dimension: {dimension}"
)

print(
    f"Index saved at: {INDEX_FILE}"
)

print(
    f"Documents saved at: {DOCUMENTS_FILE}"
)

print("\nPhase 3 embedding step completed!")