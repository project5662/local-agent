from pathlib import Path
from . import config
from . chunking import chunk_text, chunk_python_code
from . filters import should_index_file

def build_index(project_root, chroma_client, collection_name, embed_fn):
    #1
    try:
        collection = chroma_client.get_collection(collection_name)
    except Exception:
        collection = chroma_client.create_collection(collection_name)

    existing = collection.get(include=["metadatas"])

    existing_mtimes = {}
    existing_ids_by_path = {}

    for chunk_id, metadata in zip(existing["ids"], existing["metadatas"]):
        path = metadata["path"]
        existing_mtimes[path] = metadata.get("mtime")
        existing_ids_by_path.setdefault(path, []).append(chunk_id)

    all_ids = []
    all_embeddings = []
    all_metadatas = []
    all_documents = []
    seen_paths = set()

    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        if not should_index_file(path, project_root):
            continue

        relative_path = str(path.relative_to(project_root))
        seen_paths.add(relative_path)
        current_mtime = round(path.stat().st_mtime, 3)

        if existing_mtimes.get(relative_path) == current_mtime:
            continue

        if relative_path in existing_ids_by_path:
            collection.delete(ids=existing_ids_by_path[relative_path])

        try:
            content = path.read_text()
        except UnicodeDecodeError:
            continue

        if path.suffix == ".py":
            chunks = chunk_python_code(content)
            if chunks == None or chunks == []:
                chunks = chunk_text(content, config.CHUNK_SIZE_LINES, config.CHUNK_OVERLAP_LINES)

        else:
            chunks = chunk_text(content, config.CHUNK_SIZE_LINES, config.CHUNK_OVERLAP_LINES)

        
        for i, chunk in enumerate(chunks):
            embedding = embed_fn(chunk)
            all_ids.append(f"{relative_path}:{i}")
            all_embeddings.append(embedding)
            all_metadatas.append({"path": relative_path, "mtime": current_mtime})
            all_documents.append(chunk)

    deleted_paths = set(existing_mtimes.keys()) - seen_paths
    for deleted_path in deleted_paths:
        collection.delete(ids=existing_ids_by_path[deleted_path])

    if all_ids:
        collection.add(
            ids = all_ids,
            embeddings = all_embeddings,
            metadatas = all_metadatas,
            documents = all_documents
            )
    return collection

