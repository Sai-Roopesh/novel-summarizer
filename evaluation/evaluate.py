import json
import urllib.request
from urllib.error import HTTPError, URLError
from statistics import mean
from pathlib import Path

DATA_FILE = Path(__file__).with_name("sample_questions.json")


def f1_score(pred: str, truth: str) -> float:
    pred_tokens = pred.lower().split()
    truth_tokens = truth.lower().split()
    common = len(set(pred_tokens) & set(truth_tokens))
    if common == 0:
        return 0.0
    precision = common / len(pred_tokens)
    recall = common / len(truth_tokens)
    return 2 * precision * recall / (precision + recall)


def main():
    with open(DATA_FILE) as f:
        data = json.load(f)

    f1s = []
    for item in data:
        try:
            req = urllib.request.Request(
                "http://localhost:8000/ask",
                data=json.dumps({"query": item["question"]}).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req) as resp:
                ans = json.load(resp)["answer"]
        except (HTTPError, URLError) as e:
            print(f"Request failed: {e}")
            return
        f1s.append(f1_score(ans, item["answer"]))

    print("F1:", mean(f1s))


if __name__ == "__main__":
    main()
