# RPA Workflow Spec Generator

A desktop application that converts plain-English automation descriptions into structured RPA workflow specification documents — powered by the **Google Gemini API**.

Type what you want to automate, click **Generate Spec**, and get a complete, production-ready specification with objectives, scope, inputs, processing logic, outputs, design instructions, and error handling.

---

## Features

- **Natural language → structured spec** — just describe the process
- **Gemini 2.0 Flash** for fast, high-quality generation
- **Dark-themed desktop GUI** built with tkinter
- **Copy to clipboard** or **Save as .txt** with one click
- **Non-blocking UI** — API calls run in a background thread

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd rpa-spec-generator
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your API key

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder value with your actual Google Gemini API key:

```
GEMINI_API_KEY=your_actual_api_key_here
```

You can obtain a key from [Google AI Studio](https://aistudio.google.com/app/apikey).

---

## How to Run

```bash
python main.py
```

The GUI window will open. Type a description of the process you want to automate, click **Generate Spec**, and the structured specification will appear in the output area.

---

## Example

### Input

```
Automate monthly invoice processing. Read invoices from a shared email inbox,
extract vendor name, amount, and due date, validate against the vendor master
list in SAP, and post approved invoices to the ERP system. Flag any mismatches
for manual review.
```

### Expected Output

```
Workflow Name: monthly_invoice_processing

Objective
- Automate the end-to-end processing of monthly vendor invoices from email
  ingestion through ERP posting.

Scope
- Automates reading invoices from a shared email inbox, extracting key fields,
  validating against the SAP vendor master list, and posting approved invoices.
- Systems involved: Email server (Outlook/IMAP), SAP ERP, local file system.
- Does not handle invoice disputes, payment execution, or vendor onboarding.

Inputs
- Email Inbox Credentials (string) — Connection details for the shared email
  inbox containing invoices.
- SAP Vendor Master List (database connection) — Access credentials and
  connection string for the SAP vendor master table.
- ERP Posting Endpoint (string) — API endpoint or transaction code for posting
  approved invoices to the ERP system.
- Invoice Attachment Format (string) — Expected format of invoice attachments
  (e.g., PDF, XML).

Processing Logic
- Read and validate all inputs before processing.
- For each invoice email:
  - Download the invoice attachment from the email.
  - Extract vendor name, invoice amount, and due date using OCR or XML parsing.
  - Validate the extracted vendor name against the SAP vendor master list.
  - If validation passes, post the invoice to the ERP system.
  - If validation fails, flag the invoice for manual review and log the mismatch.
- Log status after each record (Success / Failed + reason).
- Handle all errors without stopping the full run.

Outputs
- ERP posting confirmation log (CSV, saved to shared drive).
- Flagged invoices report (CSV, emailed to the finance review team).
- Summary report (TXT, saved to shared drive and emailed to admin).

Design Instructions
- Validate all inputs before processing begins.
- Ensure idempotency — re-running must not cause duplicates by checking invoice
  IDs against previously posted records.
- Store all credentials in environment variables, never hardcoded.
- Include pause/resume support to avoid mid-run data loss.

Error Handling
- Log all exceptions with timestamp, record ID, and error message.
- Halt if critical config is missing (credentials, template, connection).
- Retry transient failures up to 3 times with exponential backoff.
- Send admin alert if failures exceed 20% of total records.
- Write summary report on completion: total processed, success, failed.
```

---

## Project Structure

```
rpa-spec-generator/
├── main.py              # Entry point — launches the GUI
├── gui.py               # Tkinter desktop interface
├── gemini_client.py     # Gemini API integration
├── system_prompt.py     # System prompt constant
├── .env.example         # Environment variable template
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

---

## License

MIT
