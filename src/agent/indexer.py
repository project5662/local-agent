from pathlib import Path
from . import config
from . chunking import chunk_text
from . filters import should_index_file

def build_index(project_root, chroma_client, collection_name, embed_fn):
    #1
    try:
        (chroma_client.delete_collection(collection_name))
    except Exception:
        pass
    collection = chroma_client.create_collection(collection_name)

    all_ids = []
    all_embeddings = []
    all_metadatas = []
    all_documents = []

    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        if not should_index_file(path, project_root):
            continue

        try:
            content = path.read_text()
        except UnicodeDecodeError:
            continue

        chunks = chunk_text(content, config.CHUNK_SIZE_LINES, config.CHUNK_OVERLAP_LINES)

        relative_path = str(path.relative_to(project_root))
        for i, chunk in enumerate(chunks):
            embedding = embed_fn(chunk)
            all_ids.append(f"{relative_path}:{i}")
            all_embeddings.append(embedding)
            all_metadatas.append({"path": relative_path})
            all_documents.append(chunk)

    if all_ids:
        collection.add(
            ids = all_ids,
            embeddings = all_embeddings,
            metadatas = all_metadatas,
            documents = all_documents
            )
    return collection

