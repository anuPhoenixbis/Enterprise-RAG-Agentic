import copy
import os
import json
import time

import logfire
import requests

API_URL = "http://localhost:8000/query"
STATUS_URL_TEMPLATE = "http://localhost:8000/query/status/{job_id}"
RESPONSE_TRUNCATE = 300
DELAY_BETWEEN_CALLS = 10
REQUEST_TIMEOUT = 120 #guardrails+langgraph+groq can take some time
POLL_INTERVAL = 3
MAX_POLL_ATTEMPTS = 60

def detect_tool(thought_process: list) -> str:
    """
        Maps the thought_process list from /query response to a tool name.
        Planner sets:  'Intent: Technical' + 'Search Term: ...' → retrieve_documents
                       'Intent: Conversational/Memory'           → direct_answer
        main.py sets:  'Intent: Guardrails Fired'                → guardrails
    """

    joined = " ".join(thought_process).lower() # combine are the items of the list
    if "guardrails fired" in joined:
        return "guardrails"
    if "intent: technical" in joined or "search term:" in joined or "context retrieved:" in joined:
        return "retrieve_documents"
    if "conversational" in joined or  "memory" in joined:
        return "direct_answer"
    return "unknown"

def run_pipeline(golden_dataset: dict, progress_callback=None) -> dict:
    #enriches each rag sample in golden_dataset with the API results
    #returns a deepcopy of the actual response, actual_contexts, actual_tools_called filled
    #progress_callback(i, total, question, stage,response="") is called per step

    dataset = copy.deepcopy(golden_dataset)
    #so we won't make changes to the original dataset
    samples = dataset["rag_samples"]
    n = len(samples)

    with logfire.span("Eval Phase 1 - Live Pipeline", total_samples=n):
        for i, sample in enumerate(samples):
            question = sample["question"]

            if progress_callback:
                progress_callback(i, n, question, "calling")

            with logfire.span(
                f"Live Query {i+1} of {n}",
                question=question[:80],
                domain=sample.get("domain",""),
            ):
                try:
                    #and the req to the query endpoint
                    response = requests.post(
                        API_URL,
                        json={"q": question, "thread_id": f"eval_run_{i}"},
                        timeout=REQUEST_TIMEOUT,
                    )
                    response.raise_for_status() #raises error if occurred in http
                    data = response.json()

                    raw_answer = data.get("raw_answer") or ""
                    thought_process = data.get("thought_process") or []
                    sources = data.get("sources") or []

                    sample["actual_response"] = raw_answer[:RESPONSE_TRUNCATE]
                    sample["actual_content"] = sources[:5]
                    sample["actual_tools_called"] = [detect_tool(thought_process)]

                    logfire.info(
                        "Response Captured",
                        tool=sample["actual_tools_called"][0],
                        response_chars=len(raw_answer),
                        context_chunks=len(sources),
                    )
                except requests.exceptions.ConnectionError:
                    logfire.error("Cannot reach FastAPI -> is the app running on :8000?")
                    sample["actual_response"] = ""
                    sample["actual_contexts"] = sample.get("relevant_contexts", [])
                    sample["actual_tools_called"] = ["unknown"]

                except Exception as e:
                    logfire.error(f"❌ Query failed: {e}")
                    sample["actual_response"] = ""
                    sample["actual_contexts"] = sample.get("relevant_contexts", [])
                    sample["actual_tools_called"] = ["unknown"]

            if progress_callback:
                progress_callback(i, n, question, "done" , sample["actual_response"])

            if  i < n-1:
                time.sleep(DELAY_BETWEEN_CALLS)
    return dataset


def save_results(dataset: dict, path: str) -> None:
    with open(path, "w") as f:
        json.dump(dataset, f, indent=2)

def load_golden_dataset() -> dict:
    golden_path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
    with open(golden_path, "r", encoding="utf-8") as f:
        return json.load(f)