import json
from pathlib import Path

from claude_client import analyze_barrier

EXPECTED = {
    "S1": "Access / Reimbursement",
    "S2": "Affordability",
    "S3": "Clinical Confidence",
    "S4": "Adherence / Persistence",
    "S5": "Logistics / Fulfillment",
    "S6": "Access / Reimbursement",
    "S7": "Clinical Confidence",
    "S8": "Adherence / Persistence",
    "S9": "Access / Reimbursement",
    "S10": "Awareness / Education",
}


def main():
    cases = json.loads(Path("scenarios.json").read_text())
    total = 0
    correct = 0

    for case in cases:
        result = analyze_barrier(case)
        pred = result["barrier"]
        expected = EXPECTED[case["id"]]
        is_correct = pred == expected

        total += 1
        correct += int(is_correct)

        print("=" * 80)
        print(f"Scenario: {case['id']}")
        print(f"Expected: {expected}")
        print(f"Predicted: {pred}")
        print(f"Correct: {is_correct}")
        print(f"Reason: {result['reason']}")
        print(f"Owner: {result['owner']}")
        print("Actions:")
        for action in result["actions"]:
            print(f" - {action}")

    print("=" * 80)
    print(f"Accuracy: {correct}/{total} = {correct/total:.1%}")


if __name__ == "__main__":
    main()
