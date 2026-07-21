import json
from test_data import test_cases
from classify_email import classify_email, client, MODEL, LABELS


# EXACT-MATCH CHECKER — ACCURACY: is Claude's answer the RIGHT answer?
def run_eval():
    correct = 0
    total = len(test_cases)
    consecutive_failures = 0
    eval_results = []

    for case in test_cases:
        predicted = classify_email(case["input"])
        expected = case["expected"]

        # ERROR HANDLING — skip a failed call, stop after 3 in a row
        if predicted == None:
            consecutive_failures += 1
            print(" Email classification failed — skipping this one")
            if consecutive_failures == 3:
                print("Stop the run")
                break
            continue
        else:
            consecutive_failures = 0

            # CODE-BASED GRADING — is the predicted label even a valid category?
            is_valid_label = predicted in LABELS
            if not is_valid_label:
                print(f"Invalid Label returned: {predicted}")

            # Normalized comparison — ignores case/whitespace differences
            passed = predicted.lower().strip() == expected.lower().strip()

            correct += passed
            status = "PASS" if passed else "FAIL"
            print(f"[{status}] expected: {expected}  got: {predicted}")

            # MODEL-BASED GRADING — only asked to weigh in on FAILs, to save API calls
            if status == "FAIL":
                verdict = grade_classification(case["input"], predicted, LABELS)
                print(verdict)

        # RESULTS EXPORT — collect this email's result for the JSON report
        eval_results.append({
            "email": case["input"],
            "expected": expected,
            "predicted": predicted,
            "status": status,
            "verdict": verdict if status == "FAIL" else None
        })

    accuracy = (correct / total) * 100
    print(f"Accuracy: {accuracy:.1f}%")

    # RESULTS EXPORT — write all results to a JSON file for later reference/dashboard use
    with open("eval_results.json", "w") as f:
        json.dump(eval_results, f, indent=2)


# EXACT-MATCH CHECKER — STABILITY: does Claude agree with itself across repeated calls?
def check_consistency(email_text, runs):
    results = []
    for i in range(runs):
        result = classify_email(email_text)
        results.append(result)

    set_results = set(results)
    is_consistent = len(set_results) == 1
    return results, is_consistent


# MODEL-BASED GRADING — AI JUDGE: asks Claude to review a classification for
# reasonableness, with no answer key involved (Mode B grading)
def grade_classification(email_text, predicted, labels):
    categories = ",".join(labels)
    prompt = f"""You are a QA reviewer checking an email classification.

    Email:
    {email_text}

    The classifier assigned this label: {predicted}
    Valid categories are: {categories}

    Was this a reasonable and valid classification? Reply with ONLY "Valid" or "Invalid", nothing else."""

    message = client.messages.create(
        model=MODEL,
        max_tokens=50,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return message.content[0].text.strip()


# RESULTS EXPORT — runs check_consistency() across ALL test emails and write the results to their own JSON file,
# separate from the accuracy report
def run_consistency_check(runs_per_email):
    consistency_results = []

    for case in test_cases:
        results, is_consistent = check_consistency(case["input"], runs_per_email)
        status = "consistent" if is_consistent else "not_consistent"
        consistency_results.append({
            "email": case["input"],
            "results": results,
            "status": status
        })

    with open("consistency_results.json", "w") as f:
        json.dump(consistency_results, f, indent=2)


if __name__ == "__main__":
    # 1. Accuracy check across all test emails
    run_eval()

    # 2. Consistency check across all test emails
    runs_per_email = int(input("How many times to test each email? "))
    run_consistency_check(runs_per_email)
