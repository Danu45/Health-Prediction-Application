# Health Prediction Application

A simple patient blood-test record management application built with Python, Streamlit, SQLite and the Google Gemini API.

> **Safety note:** This is an educational demonstration, not a diagnostic medical tool. It does not calculate validated disease probabilities. AI remarks are informational and may be wrong.

## Features

- Create, read, update and delete patient records (CRUD).
- SQLite persistent storage.
- Validation for required name, email format, real date of birth, future dates, and non-negative numeric test values.
- Normal form requires `dd/mm/yyyy`.
- The assignment's original test data is stored unchanged in `test_data.csv` and uses `dd.mm.yyyy`; the importer validates that source format without changing the supplied source file.
- Duplicate detection based on matching full name, date of birth and email.
- Gemini API integration for cautious informational remarks.
- Clear fallback remarks if the API key is missing, the API is unavailable, or a request fails.
- Persistent import log showing created/rejected test rows and reasons.
- CSV export of saved records.

## Setup

Requires Python 3.10 or newer.

### 1. Open a terminal in this project folder

Create and activate a virtual environment.

**Windows PowerShell**
```powershell
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**macOS/Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Gemini

1. Copy `.env.example` to a new file named `.env`.
2. Create/get an API key through Google AI Studio.
3. Put the key after `GEMINI_API_KEY=` in `.env`.
4. Keep `.env private. Do not upload it to GitHub or share it in screenshots.

Without a configured key, CRUD still works. Remarks will clearly say that AI remarks are unavailable rather than pretending a prediction was generated.

### 3. Run

```bash
streamlit run app.py
```

Streamlit prints a local URL (usually `http://localhost:8501`) to open in a browser.

## Assignment test-data walkthrough

1. Open **Assignment test data**.
2. Click **Process supplied 10 test rows**.
3. Review the latest results and persistent validation log.
4. Open **Read records** to see successfully created records.
5. Use **Update** to change a valid record's email to `gokul@infocare.com`.
6. Use **Delete** to delete one record, confirm deletion, then revisit **Read records**.

### Expected validation behavior

- **Test 1 — Robyn Pears:** valid input; created unless it already exists.
- **Test 2 — John Hunter:** rejected because `hunter@gmail` has no domain suffix such as `.com`.
- **Test 3 — Darryl Tim:** valid formats and numeric values; created unless duplicate.
- **Test 4 — Peter Larry:** rejected because 31 November is not a real calendar date.
- **Test 5 — Sam Kerr:** valid formats and numeric values; created unless duplicate.
- **Test 6 — Robyn Pears:** rejected as a duplicate of Test 1 if Test 1 is already saved.
- **Test 7 — Madison XI:** valid formats and numeric values; created unless duplicate. A haemoglobin result that looks unusual is not rejected merely because it is unusual.
- **Test 8 — Kris Wu:** rejected because DOB is in the future and `Kris.wu.gmail.com` is not a valid email address.
- **Test 9 — Tenille Singh:** valid formats and numeric values; created unless duplicate.
- **Test 10 — Prem Kumar:** valid formats and numeric values; created unless duplicate.

The numeric fields are validated for numeric, non-negative values, not as medical reference-range checks. The assignment does not specify units or fasting status, so the app must not make definitive diagnoses from these numbers.

If you run the import a second time, records that were already saved are reported as duplicates instead of being added again. The import log is retained in SQLite.

## Manual test checklist

| Test | Steps | Expected result |
|---|---|---|
| Create valid record | Enter valid name, date, email and numeric values | Saved to SQLite; remarks generated if Gemini is configured |
| Empty name | Submit blank name | Validation error; no save |
| Invalid email | Enter `hunter@gmail` | Validation error; no save |
| Wrong form date format | Enter `28.01.1960` in the normal form | Date-format error; normal form requires `dd/mm/yyyy` |
| Impossible date | Enter `31/11/2001` | Invalid calendar date error |
| Future DOB | Enter a date after today | Future DOB error |
| Non-numeric glucose | Enter `abc` | Numeric validation error |
| Negative cholesterol | Enter `-1` | Non-negative numeric validation error |
| Read | Open Read records | All currently saved records displayed |
| Update | Change email to `gokul@infocare.com` and save | Updated email persists |
| Delete | Select a record, tick confirmation, delete | Record no longer appears in list |
| API missing | Remove/omit Gemini key and create record | CRUD still works; remarks state AI unavailable |
| API failure | Use invalid key or no network | Error handled gracefully; no app crash |

## Database design

### `patients`
- `id`: auto-increment primary key
- `full_name`
- `date_of_birth`
- `email`
- `glucose`
- `haemoglobin`
- `cholesterol`
- `remarks`
- `created_at`
- `updated_at`

### `import_logs`
Stores the original test number, name, original DOB/email, status, reason, and timestamp for each import attempt. This makes rejected inputs and duplicate handling easy to demonstrate.

## Code overview for interviews

- `app.py`: UI tabs and orchestration of CRUD and test-data import.
- `database.py`: SQLite schema and parameterized SQL statements.
- `validation.py`: input checks and conversion of valid input to consistent data types.
- `ai_service.py`: Gemini client call, prompt restrictions, and error handling.
- `test_data.csv`: exact source rows provided by the assignment.

### Why SQLite?
SQLite is a lightweight relational database stored in a local file. It needs no separate database server and preserves records across app restarts.

### Why use parameterized SQL?
Values are passed separately from SQL statements, reducing SQL injection risk and avoiding fragile string concatenation.

### Why are validation errors not saved as patient records?
Invalid input should not become a patient record. The import log records the test number and reason so the interviewer can still see exactly why a row was rejected.

### Why no definite disease prediction?
The assignment does not specify test units, reference ranges, fasting status, patient context, or a validated prediction model. Gemini is used to generate cautious educational remarks, not a medically validated disease probability.

## Interview demonstration script

1. “This is a Python and Streamlit application with SQLite persistence and Gemini API integration.”
2. Create a valid record and show it in **Read records**.
3. Explain that `validate_patient()` checks date format, calendar validity, future dates, email syntax and numeric fields before a database insert.
4. Run the supplied dataset. Show the invalid email, impossible date, duplicate, and future DOB errors in the log.
5. Explain that source test dates are preserved in `test_data.csv` in the supplied dot-separated format, while the normal user form follows the required slash-separated format.
6. Update a record's email to `gokul@infocare.com`.
7. Delete a record and show the remaining list.
8. Explain that Gemini errors do not crash the app and that the UI does not claim a diagnosis.
9. Explain that the SQLite database is local and `.env` is excluded from Git.

## Important limitations

- Email validation checks syntax, not whether an inbox exists.
- Numeric checks do not confirm clinical units or whether a value is medically normal.
- Gemini responses are not validated medical predictions.
- A production healthcare system would need authentication, authorization, encryption, audit controls, consent, retention policies, and appropriate privacy/regulatory review.
