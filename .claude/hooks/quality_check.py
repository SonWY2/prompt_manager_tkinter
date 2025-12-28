import sys
import os

REPORT_FILE = "docs/validation_report.txt"

def main():
    if not os.path.exists(REPORT_FILE):
        print(f"Error: {REPORT_FILE} not found.")
        sys.exit(1) # File missing error

    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Validator가 FAIL을 기록했는지 확인
    if "STATUS: FAIL" in content or "REJECT" in content:
        print("\n[HOOK] Quality Check Failed. Please review the validation report.")
        print("-" * 40)
        print(content)
        print("-" * 40)
        sys.exit(2) # Quality Check Fail -> Stops the pipeline

    print("\n[HOOK] Quality Check Passed.")
    sys.exit(0) # Success

if __name__ == "__main__":
    main()