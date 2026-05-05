import json
import sys
import os
from datetime import datetime
from pathlib import Path
import asyncio
import httpx
import pandas as pd
from dotenv import load_dotenv

from ragas import evaluate
from ragas.metrics import faithfulness, context_precision, context_recall
from ragas.llms import LangchainLLMWrapper
from langchain_ollama import ChatOllama

from datasets import Dataset

load_dotenv()
Golden_Set_Path = Path(__file__).parent / "golden_set" / "qa.jsonl"
Results_Dir = Path(__file__).parent / "results"
Results_Dir.mkdir(exist_ok=True)

# Checkpoint file — stores RAG responses so a crash doesn't lose progress
CHECKPOINT_PATH = Results_Dir / "rag_responses_checkpoint.json"
Api_Base_Url = os.getenv("API_BASE_URL", "http://127.0.0.1:5555")
tenant = "Hiaw_8NBx5QaiIYSwfbx_1pmxPYnFY6a" 
Chat_Endpoint = f"{Api_Base_Url}/chat"
Timeout = 60.0

HEADERS = {"x-api-key":tenant} if tenant else {}

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://lugged-guide-although.ngrok-free.dev/")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "gemma3:1b")


async def load_golden_set(jsonl_path: Path) -> list[dict]:
    questions = []
    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    questions.append(json.loads(line))
        print(f" Loaded {len(questions)} questions from Dataset")
        return questions
    except FileNotFoundError:
        print(f"File not found at {jsonl_path}")
        sys.exit(1)


def load_checkpoint() -> dict:
    """Load previously saved RAG responses keyed by question text."""
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f" Checkpoint found — resuming from {len(data)} saved responses")
        return data
    print(" No checkpoint found — starting fresh")
    return {}


def save_checkpoint(checkpoint: dict) -> None:
    """Persist the checkpoint to disk immediately after each RAG response."""
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)


async def get_answer_from_rag(question: str) -> tuple[str, list[str]]:
    try:
        async with httpx.AsyncClient(timeout=Timeout) as client:
            response = await client.post(
                Chat_Endpoint,
                json={"query": question},
                headers=HEADERS
            )
            response.raise_for_status()
            data = response.json()

            answer = data.get("answer", "")
            contexts = []
            for citation in data.get("citations", []):
                snippet = citation.get("snippet") or citation.get("text", "")
                if snippet:
                    contexts.append(snippet)

            return answer, contexts

    except Exception as e:
        print(f" Failed to get answer for '{question[:20]}...': {str(e)}")
        return "", []


async def run_evaluation(questions: list[dict]) -> pd.DataFrame:
    results = []
    total = len(questions)
    checkpoint = load_checkpoint()

    print(f"\n Running RAG Pipeline on {total} questions...")

    for idx, item in enumerate(questions, 1):
        question = item["question"]
        reference = item["reference"]
        source = item.get("source", "unknown")

        # --- Resume from checkpoint if this question was already answered ---
        if question in checkpoint:
            cached = checkpoint[question]
            answer = cached["answer"]
            contexts = cached["contexts"]
            print(f"   [{idx}/{total}] (checkpoint) {question[:50]}...")
        else:
            answer, contexts = await get_answer_from_rag(question)

            if not answer:
                print(f"   [{idx}/{total}] No answer returned for: {question[:25]}...")
                continue

            # Save immediately — if the run crashes, this response is safe
            checkpoint[question] = {"answer": answer, "contexts": contexts}
            save_checkpoint(checkpoint)
            print(f"   [{idx}/{total}] (fetched)     {question[:50]}...")

        results.append({
            "question": question,
            "answer": answer,
            "contexts": contexts,
            "reference": reference,
            "source": source,
        })

    print(f" Collected {len(results)} Q&A pairs from RAG pipeline")
    return pd.DataFrame(results)


def run_ragas_metrics(df: pd.DataFrame) -> dict:
    print(f"\n Running RAGAS metrics using Ollama ({OLLAMA_LLM_MODEL})...")

    evaluator_llm = LangchainLLMWrapper(ChatOllama(
        model=OLLAMA_LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        timeout=300,    # 5 min per call — ngrok + Colab can be slow
        num_ctx=4096,   # keep context window manageable
    ))

    ragas_data = {
        "user_input": df["question"].tolist(),
        "retrieved_contexts": df["contexts"].tolist(),
        "response": df["answer"].tolist(),
        "reference": df["reference"].astype(str).tolist(),
    }

    dataset = Dataset.from_dict(ragas_data)

    results = evaluate(
        dataset,
        metrics=[faithfulness, context_precision, context_recall],
        llm=evaluator_llm,
        batch_size=1,           # one sample at a time — prevents Ollama overload
        raise_exceptions=False, # log failures, don't crash the whole run
    )
    return results


def _to_series(value, length: int) -> list:
    """Normalise a metric value to a plain list of floats.

    RAGAS can return:
      - a list of per-sample floats  → use as-is
      - a single float (aggregate)   → broadcast to every row
      - None / NaN                   → fill with NaN so the CSV still lines up
    """
    import math
    if isinstance(value, list):
        return value
    if isinstance(value, float) and not math.isnan(value):
        return [value] * length
    return [float("nan")] * length


def _mean(values: list) -> float:
    """Mean of a list, ignoring NaNs."""
    import math
    clean = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    return sum(clean) / len(clean) if clean else float("nan")


def save_results(df: pd.DataFrame, metrics_results: dict) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = Results_Dir / f"ragas_results_{timestamp}.csv"

    n = len(df)
    scores_df = metrics_results.to_pandas()
    faith = scores_df["faithfulness"].tolist()
    cp    = scores_df["context_precision"].tolist()
    cr    = scores_df["context_recall"].tolist()

    df["faithfulness"]      = faith
    df["context_precision"] = cp
    df["context_recall"]    = cr

    df.to_csv(csv_path, index=False)

    print(f"\nResults saved to {csv_path}")
    print("\n" + "-" * 30)
    print("Aggregate Scores:")
    print(f"    Faithfulness:      {_mean(faith):.4f}")
    print(f"    Context Precision: {_mean(cp):.4f}")
    print(f"    Context Recall:    {_mean(cr):.4f}")
    print("-" * 30)

    return csv_path


async def main():
    print("=" * 60)
    print("DocMind RAGAS Evaluation (Ollama)")
    print("=" * 60)

    print(f"\n Checking API at {Api_Base_Url}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{Api_Base_Url}/", timeout=10.0)
            print(" API is running fine")
    except Exception as e:
        print(f" API not accessible: {str(e)}")
        sys.exit(1)

    questions = await load_golden_set(Golden_Set_Path)

    if not questions:
        print("No questions loaded. Exiting.")
        sys.exit(1)

    df_results = await run_evaluation(questions)

    if df_results.empty:
        print("No results collected. Check API and Golden Set.")
        sys.exit(1)

    metrics_results = run_ragas_metrics(df_results)
    csv_path = save_results(df_results, metrics_results)

    print(f"\nEvaluation Complete: {csv_path}")


if __name__ == "__main__":
    asyncio.run(main())