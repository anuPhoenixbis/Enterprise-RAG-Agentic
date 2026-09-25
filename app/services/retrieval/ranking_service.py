import time
import logfire
from flashrank import Ranker, RerankRequest

#lazy initialization :  ranker is loaded on first use to ensure logfire.configure works
_ranker = None

def _get_ranker() -> Ranker:
    #init flashrank engine lazily, becoz too computationally expensive
    # flashrank uses a local ONNX model for ultra fast reranking

    global _ranker
    if _ranker is None:
        logfire.info("Initializing FlashRank Model (TinyBERT) locally..")
        try:
            #we use a cache dir to avoid permissions issues in prod
            _ranker = Ranker(cache_dir="/temp/flashrank")
        except Exception:
            _ranker = Ranker()
    return _ranker

def rerank_documents(query: str, documents: list[str], top_n: int = 5) -> list[str]:
    #refines retrieval results by re-scoring docs against the query semantically
    #standard cosine similarity vector search is fast but mathematically "fuzzy"
    #flashrank uses Cross-Encoder approach which is much more precise but usually requires too much computations
    #flashrank solves this by using highly optimized, quantized ONNX models locally

    if not documents: return []

    start_time = time.time() #get the current time
    logfire.info(f"[Reranker] Sending {len(documents)} documents to FlashRank...")

    try:
        ranker = _get_ranker()

        #flashrank expects a list of dict with id and text
        passages = [
            {"id": i, "text" : doc}
            for i, doc in enumerate(documents)
        ]

        request = RerankRequest(query=query, passages=passages)
        results = ranker.rerank(request)

        #results are returned sorted by highest semantic score first
        reranked_docs = []
        for res in results[:top_n]:
            reranked_docs.append(res["next"])

        duration = time.time() - start_time #time taken
        top_score = results[0]["score"] if results else 'N/A'
        logfire.info(f"[Reranker] Done in {round(duration, 2)} seconds. Top semantic score: {top_score}")

        return reranked_docs
    except Exception as e:
        logfire.error(f"[Reranker] Semantic Reranking Failed: {e}")
        return documents[:top_n]  #just do the regular top_k