"""Real Foundation Model 125-Inference Empirical Benchmark Suite."""

import json
import statistics
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

url = "http://localhost:1234/v1/chat/completions"
model = "gemma-4-e4b-it-ultra-uncensored-heretic"

test_prompts = [
    # Logic & Reasoning (5)
    ("reasoning", "If all Bloops are Razzies and all Razzies are Lurgs, are all Bloops definitely Lurgs? Answer in 1 word: Yes or No."),
    ("reasoning", "A bat and ball cost $1.10. The bat costs $1.00 more than the ball. How much does the ball cost in cents? Answer only the number."),
    ("reasoning", "Which is heavier: a pound of feathers or a pound of gold? Explain in 1 sentence."),
    ("reasoning", "If you have 3 apples and you take away 2, how many apples do you have? Answer only the number."),
    ("reasoning", "If a train leaves at 2 PM traveling 60 mph, how far does it travel by 5 PM? Answer only the number of miles."),
    # Consistency / Repetition (5)
    ("consistency", "State the capital of France in 1 word."),
    ("consistency", "State the chemical symbol for Gold in 1 word."),
    ("consistency", "State the speed of light in vacuum in km/s (approximate number only)."),
    ("consistency", "State the binary representation of decimal 5 in 1 word."),
    ("consistency", "What is 12 multiplied by 12? Number only."),
    # Coding & Algorithms (5)
    ("coding", "Write a Python one-liner to reverse a string s."),
    ("coding", "Write a Python function to check if a number is prime."),
    ("coding", "What is the time complexity of quicksort in the average case? Format: O(...)"),
    ("coding", "How do you check if a key exists in a Python dict d? Code snippet only."),
    ("coding", "Write a Python list comprehension to filter even numbers from numbers list."),
    # Tool / Structured Output (5)
    ("structured", "Return a JSON with keys status (string 'ok') and count (int 42). JSON only."),
    ("structured", "Return a JSON with keys verified (bool true) and system (string 'Alpha'). JSON only."),
    ("structured", "Return a JSON with keys priority (string 'HIGH') and score (float 0.95). JSON only."),
    ("structured", "Return a JSON with keys action (string 'EXECUTE') and target (string 'sandbox'). JSON only."),
    ("structured", "Return a JSON with keys verdict (string 'APPROVED') and risk_level (int 1). JSON only."),
    # Hallucination / Factuality (5)
    ("factuality", "Did Leonardo da Vinci invent the iPhone? Answer Yes or No."),
    ("factuality", "What year did World War II end? Year only."),
    ("factuality", "Is water composed of Hydrogen and Oxygen? Answer Yes or No."),
    ("factuality", "Can humans survive without oxygen for 1 hour? Answer Yes or No."),
    ("factuality", "Who wrote the play Hamlet? Name only.")
]

# Generate 125 total inferences (5 cycles of 25 prompts)
inferences = []
for cycle in range(5):
    for category, prompt in test_prompts:
        inferences.append((len(inferences) + 1, category, prompt))

def execute_single_inference(item):
    idx, cat, prompt = item
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.1
    }
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload).encode("utf-8"))
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            dt = (time.time() - t0) * 1000.0
            msg = data["choices"][0]["message"]
            content = msg.get("content") or msg.get("reasoning_content") or ""
            tokens_in = data.get("usage", {}).get("prompt_tokens", 0)
            tokens_out = data.get("usage", {}).get("completion_tokens", 0)
            return {
                "id": idx, "cat": cat, "success": True, "latency_ms": dt,
                "tokens_in": tokens_in, "tokens_out": tokens_out, "content": content.strip(),
                "has_reasoning": bool(msg.get("reasoning_content"))
            }
    except Exception as e:
        return {
            "id": idx, "cat": cat, "success": False, "latency_ms": (time.time() - t0) * 1000.0,
            "tokens_in": 0, "tokens_out": 0, "content": str(e), "has_reasoning": False
        }

if __name__ == "__main__":
    print(f"Starting 125 real foundation model inferences with 8 worker threads...")
    t_start = time.time()
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(execute_single_inference, inferences))
    total_time = time.time() - t_start

    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    latencies = [r["latency_ms"] for r in successes]

    p50 = statistics.median(latencies) if latencies else 0
    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else 0
    mean_lat = statistics.mean(latencies) if latencies else 0

    print(f"COMPLETED {len(results)} INFERENCES IN {round(total_time, 2)}s!")
    print(f"SUCCESSFUL: {len(successes)} / {len(results)} ({round(len(successes)/len(results)*100, 1)}%)")
    print(f"FAILED: {len(failures)}")
    print(f"LATENCY: mean={round(mean_lat, 1)}ms | p50={round(p50, 1)}ms | p95={round(p95, 1)}ms")
    print(f"THROUGHPUT: {round(len(results) / total_time, 2)} req/s")

    print("\nSAMPLE INFERENCE RESULTS:")
    for r in successes[:8]:
        print(f"[{r['cat']}] ID {r['id']}: {r['content'][:60]} (Latency: {round(r['latency_ms'])}ms)")

    output_path = "data/benchmark_125_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "total": len(results),
            "success_count": len(successes),
            "total_time_s": round(total_time, 2),
            "mean_latency_ms": round(mean_lat, 1),
            "p50_ms": round(p50, 1),
            "p95_ms": round(p95, 1),
            "results": results
        }, f, indent=2)
    print(f"\nPersisted benchmark metrics to {output_path}")
