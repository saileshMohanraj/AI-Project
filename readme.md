# Clinic Visit Sorter

## 1. Project Overview

Clinic Visit Sorter is a Python-based project that organizes student clinic visits according to their reported symptoms and urgency.

It uses the Gemini API to classify visit notes into categories and priorities. Python applies additional safety rules to identify red-flag symptoms and raise their priority when necessary.

The system is designed to help nurses organize visits. It does not diagnose diseases or replace medical professionals.

## 2. Technologies Used

- Python
- Google Gemini API
- CSV for input and output data
- JSON for structured LLM responses
- Git and GitHub

## 3. Project Structure

```text
clinic-visit-sorter/
│
├── data/
│   └── visits.csv
│
├── reports/
│   ├── nurse_queue.csv
│   └── summary.txt
│
├── src/
│   ├── data_loader.py
│   ├── classifier.py
│   ├── validator.py
│   ├── priority.py
│   ├── safety.py
│   ├── report_generator.py
│   ├── evaluation.py
│   └── red_team.py
│
├── .env
├── .gitignore
├── app.py
└── readme.md
```

## 4. How the System Works

1. Load student visit notes from a CSV file.
2. Send each note to the Gemini API.
3. Classify the note into a predefined category.
4. Assign a priority: `see_now`, `today`, or `routine`.
5. Validate the LLM response.
6. Check the original note for red-flag symptoms.
7. Raise priority when safety rules require it.
8. Generate the nurse queue and summary reports.

## 5. Classification Categories

| Category | Description |
|---|---|
| injury | Physical injuries |
| fever_cold | Fever, cold and related symptoms |
| stomach | Stomach-related complaints |
| pain | General pain complaints |
| allergy | Allergy-related symptoms |
| other | Unclassified or unclear complaints |

## 6. Priority Levels

| Priority | Meaning |
|---|---|
| see_now | Requires immediate nurse attention |
| today | Requires review during the current day |
| routine | Lower urgency for nurse review |

## 7. Judgment Framework

| Situation | System action | Reason |
|---|---|---|
| Chest pain or breathing difficulty | see_now | Red-flag symptoms |
| Fainting or severe bleeding | see_now | Requires immediate attention |
| Mild fever or stomach pain | today | Requires nurse review |
| Mild, non-urgent symptoms | routine | Lower urgency |
| Unknown or unclear input | At least today | Avoid unsafe under-prioritisation |
| LLM/API failure | today fallback | Never assume the visit is routine |
| Python detects a higher-risk symptom | Raise priority | Safety rules take precedence |

**Important rule:** Python can raise the priority but must never lower it.

## 8. Safety and Red-Team Testing

The project includes tests for:

1. Prompt injection: Attempts to manipulate the system into marking a visit as routine.
2. Diagnosis request: Checks handling of a request to identify a disease.
3. Tamil red-flag input: Tests recognition of the phrase `Enakku nenju vali irukku`.

The red-team tests check whether the Python safety layer behaves as expected.

## 9. Evaluation

An evaluation script is included to test five sample visit notes.

It compares the predicted category and final priority against expected values and calculates the number of correct classifications.

Evaluation requires a working Gemini API connection and available quota.

## 10. Cost and Latency Considerations

- The project uses the Gemini API.
- API usage is subject to the model's free-tier limits and applicable quotas.
- Each classification requires an API request, so processing time increases with the number of visits.
- A delay between requests helps reduce rate-limit errors.
- Temporary API failures are handled using a retry.
- If the API quota is exhausted, the application uses a conservative `today` fallback priority.
- Red-flag checks continue even when Gemini is unavailable.

## 11. Human Checkpoint

This project is an educational simulation, not a medical diagnostic or autonomous triage system.

Every visit must be reviewed by a nurse. The nurse makes the final decision about the patient's care.

The system only helps organize visits for human review.

## 12. Running the Project

Activate the virtual environment and install the required packages.

```bash
pip install -r requirements.txt
```

Add your Gemini API key to the `.env` file:

```text
GEMINI_API_KEY=your_api_key_here
```

Run the application:

```bash
python app.py
```

Run the red-team tests:

```bash
python src/red_team.py
```

Run the evaluation when Gemini API access is available:

```bash
python src/evaluation.py
```

## 13. Conclusion

Clinic Visit Sorter demonstrates how an LLM can be combined with Python-based validation and safety rules to organize student clinic visits.

The project emphasizes structured output, priority escalation, prompt-injection awareness, API failure handling, and human oversight.
