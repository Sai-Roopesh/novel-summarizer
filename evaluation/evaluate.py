import json
import requests
from statistics import mean

DATA_FILE = "sample_questions.json"


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
        resp = requests.post(
            "http://localhost:8000/ask", json={"query": item["question"]}
        )
        resp.raise_for_status()
        ans = resp.json()["answer"]
        f1s.append(f1_score(ans, item["answer"]))

    print("F1:", mean(f1s))


if __name__ == "__main__":
    main()
