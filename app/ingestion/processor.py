#it is used to convert 1 type of file to another
# hence the name smart_parser
import os
import sys
import uuid
import json
import logfire

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.config import settings
from app.services.retrieval.embeddings import embed_texts, get_embedding_dim
from app.ingestion.loaders.pdf import parse_pdf
from app.ingestion.loaders.html import parse_html
from app.ingestion.loaders.text import parse_text
from app.ingestion.chunking.splitter import chunk_text

logfire.configure(service_name="enterprise-ingestion-service")
#storing in the qdrant cloud and storing locally in a dir

PROCESSED_DATA_DIR = "processed_data"

qdrant_client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
)

def save_processed_locally(data: dict, source_type: str, filename: str)-> str:
    # save the parsed chunk metadata as JSON in processed_data/<source_type>/.
    folder = os.path.join(PROCESSED_DATA_DIR, source_type)
    os.makedirs(folder, exist_ok=True)
    dest = os.path.join(folder, f"{filename}.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logfire.info(f"Saved {filename} to {dest}")
    return dest

def process_file(file_path: str, filename: str, source_type: str):
    # parse -> chunk -> save locally -> embed -> ind in Qdrant
    with logfire.span("Processing File", file = filename, source = source_type):
        try:
            #grab the extension to identify the file type
            ext = filename.lower().rsplit(".",1)[-1]
            if ext == "pdf":
                full_text = parse_pdf(file_path)
            elif ext == "html":
                full_text = parse_html(file_path)
            elif ext == "txt":
                full_text = parse_text(file_path)
            elif ext in ("docx","pptx"):
                from app.ingestion.loaders.office import parse_office
                full_text = parse_office(file_path)
            else:
                logfire.warning(f"Unrecognized file extension: {ext}")
                return

            if not full_text or not full_text.strip():
                logfire.warning(f"Empty text for {filename}-skipping")
                return

            #chunk text
            chunks = chunk_text(full_text)
            if not chunks: return

            processed_data = {
                "filename": filename,
                "source_type": source_type,
                "chunks": chunks,
            }

            local_path = save_processed_locally(processed_data, source_type, filename)
            logfire.info(f"Saved {filename} to {local_path}")

            with logfire.span("Vectorizing & Indexing"):
                embeddings = embed_texts(chunks)
                points = [
                    # its like a data point in the vector search db
                    models.PointStruct(
                        id = str(uuid.uuid4()),
                        vector=vector,
                        payload={
                            "text": chunk,
                            "source": filename,
                            "source_type": source_type,
                        }
                    )
                    for chunk, vector in zip(chunks, embeddings)
                ]
                qdrant_client.upsert(
                    collection_name=settings.QDRANT_COLLECTION,
                    points=points #push the pts
                )

                logfire.info(f"Indexed {len(points)} points to Qdrant from {filename}")
        except Exception as e:
            logfire.error(f"Error processing {filename}: {e}")


def process_directory(dir_path: str, source_type: str):
    # process every file in a dir
    with logfire.span("Scanning Directory", path = dir_path, source=source_type):
        files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path,f))]
        logfire.info(f"Found {len(files)} files in {dir_path}")
        for file in files:
            process_file(os.path.join(dir_path, file), file, source_type)

def run_universal_ingestion(base_dir: str, explicit_source_type: str = None, wipe: bool = False):
    # scan base_dir, map sub-folders to source types, and ingest all docs.
    # pass -wipe to drop and recreate the qdrant collection before ingestion

    with logfire.span("Universal Ingestion Started", path = base_dir):
        if not qdrant_client.collection_exists(settings.QDRANT_COLLECTION):
            dim = get_embedding_dim()
            qdrant_client.create_collection(
                settings.QDRANT_COLLECTION,
                vectors_config = models.VectorParams(
                    size=dim,
                    distance=models.Distance.COSINE #using the cosine similarity search
                )
            )
            logfire.info(
                f"Created {settings.QDRANT_COLLECTION} collection"
                f"({dim}-dim, Cosine)"
            )

        subdirs = [
            d for d in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, d))
        ]

        if not subdirs:
            if explicit_source_type:
                source_type = explicit_source_type
            else:
                base_name = os.path.basename(os.path.normpath(base_dir)).lower()
                source_type = (
                    "true" if "true" in base_name
                    else "noisy" if "noisy" in base_name
                    else "general"
                )
            logfire.info(f"No sub-folders found - processing '{base_dir}' as '{source_type}'")
            process_directory(base_dir, source_type)
        else:
            for subdir in subdirs:
                source_type=(
                    "true" if "true" in subdir.lower()
                    else "noisy" if "noisy" in subdir.lower()
                    else subdir
                )
                process_directory(os.path.join(base_dir, subdir), source_type)

if __name__ == "__main__":
    # to the processors and get and parse the docs
    wipe_requested = "--wipe" in sys.argv
    clean_args = [arg for arg in sys.argv if arg != "--wipe"] #clear args if there is any --wipe

    target_dir = clean_args[1] if len(clean_args) > 1 else "DATA"
    explicit_type = clean_args[2] if len(clean_args) > 2 else None

    if not os.path.exists(target_dir):
        print(f"Error: path '{target_dir}' does not exist.")
        sys.exit(1)

    run_universal_ingestion(target_dir, explicit_type, wipe_requested)
    logfire.info("Ingestion job completed")