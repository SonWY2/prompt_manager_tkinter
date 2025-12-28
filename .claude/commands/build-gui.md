---
description: Python Tkinter GUI 개발 파이프라인을 실행합니다.
allowed-tools: Task, Read, Write, Bash, Agent
---

# 🚀 GUI Build Pipeline Start: "$ARGUMENTS"

## Step 1: Requirements Analysis (PM)
@agent:pm-spec.md
Instruction:
1. Read the user request: "$ARGUMENTS"
2. Create or update `docs/architecture.md`.
3. Ensure requirement clearly defines the inputs and outputs.

## Step 2: UI Design (Designer)
@agent:gui-designer.md
Instruction:
1. Read `docs/architecture.md`.
2. Append a "UI Layout Specification" section to `docs/architecture.md`.
3. Detail the widget hierarchy and Tkinter geometry manager strategy (pack vs grid).

## Step 3: Implementation (Developer)
@agent:dev-python.md
Instruction:
1. Read the full `docs/architecture.md`.
2. Write the complete code in `src/main.py`.
3. Ensure the code is self-contained and runnable.

## Step 4: Validation (QA)
@agent:validator.md
Instruction:
1. Read `src/main.py` and `docs/architecture.md`.
2. Analyze if the code meets requirements and is bug-free.
3. Write your evaluation to `docs/validation_report.txt`. 
4. **CRITICAL**: If the code is flawed, write "STATUS: FAIL" at the top. If good, write "STATUS: PASS".

## Step 5: Quality Gate Check
Run command: `python3 .claude/hooks/quality_check.py`

If the command fails (exit code 2), print:
"⚠️ Validation FAILED. Requesting re-work..."
(Here you might want to loop back to Step 3 manually or automatically depending on tool capability)

If success:
"✅ Build Complete! You can run the app with: python src/main.py"