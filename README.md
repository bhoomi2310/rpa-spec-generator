# RPA Workflow Spec Generator

A desktop application that converts plain-English automation descriptions into structured RPA workflow specification documents or matches and executes pre-defined workflows using the **Google Gemini API**.

---

## Features

- **Spec Generator Tab** — Natural language → structured spec (generates complete, production-ready specifications with objectives, scope, inputs, processing logic, outputs, design instructions, and error handling).
- **Run Automation Tab** — Intent Detection + Automation Catalog (automatically matches your natural language request to pre-defined workflows, renders a dynamic form, and runs a local simulation).
- **Gemini 2.5 Flash** for fast, high-quality generation and matching.
- **Dark-themed desktop GUI** built with tkinter.
- **Non-blocking UI** — API calls run in background threads.

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

The GUI window will open with a tab bar at the top:
1. **Spec Generator**: Type a description of the process you want to automate, click **Generate Spec**, and the structured specification will appear.
2. **Run Automation**: Type what you want to execute (e.g. "onboard John Doe"), click **Find Automation**, fill in the dynamic input form, and click **Run Automation** to see a simulated log.

---

## Automation Catalog Feature

The application contains an offline automation catalog of 10 standard workflows.

### Intent Detection Flow
1. When you enter a prompt in the "Run Automation" tab, the prompt is evaluated against the catalog schema by Gemini.
2. The model detects which catalog item best fits the intent of the prompt based on names, descriptions, and keywords.
3. If matched, the GUI dynamically constructs a custom form using tkinter widgets based on the required fields.
4. If no match is found, the system displays an error message allowing you to quickly switch to the "Spec Generator" tab to build a new workflow specification.

### Adding New Automations
You can add your own automations by editing [automations_catalog.json](file:///C:/Users/imbho/.gemini/antigravity-ide/scratch/rpa-spec-generator/automations_catalog.json). Every automation entry must follow this structure:

```json
  {
    "id": "unique_snake_case_id",
    "name": "Human Readable Name",
    "description": "One sentence description of the workflow.",
    "keywords": ["keyword1", "keyword2"],
    "required_inputs": [
      {
        "field": "field_name",
        "label": "Display Label",
        "type": "text", // "text", "email", "date", "number", or "dropdown"
        "placeholder": "Example placeholder text"
      },
      {
        "field": "dropdown_field",
        "label": "Dropdown Label",
        "type": "dropdown",
        "options": ["Option A", "Option B"],
        "placeholder": "Select option"
      }
    ],
    "expected_outputs": [
      "Description of output 1",
      "Description of output 2"
    ]
  }
```

### Simulation Execution Output
Clicking "Run Automation" simulates the execution locally and writes detailed execution logs. The simulated output has the following structure:

```
==================================================================
AUTOMATION TRIGGERED: [Name of Matched Automation]
==================================================================
Timestamp: YYYY-MM-DD HH:MM:SS
Status:    SUCCESS

[INPUTS RECEIVED]
  • [Input Label 1]: [Value 1]
  • [Input Label 2]: [Value 2]

[STEPS EXECUTED]
  1. [Step 1 description with dynamic values]
  2. [Step 2 description with dynamic values]
  3. [Step 3 description with dynamic values]
  4. [Step 4 description with dynamic values]

[OUTPUTS GENERATED]
  • [Output Description 1]:
    -> [Dynamic dummy output result 1]
  • [Output Description 2]:
    -> [Dynamic dummy output result 2]
==================================================================
```

---

## Project Structure

```
rpa-spec-generator/
├── main.py                   # Entry point — launches the GUI
├── gui.py                    # Tabbed Tkinter desktop GUI
├── gemini_client.py          # Gemini API integration for generating specs
├── catalog_client.py         # Catalog helper & local simulation logic
├── system_prompt.py          # System prompt constant for Spec generation
├── automations_catalog.json  # Database of pre-defined automations
├── .env.example              # Environment variable template
├── requirements.txt          # Python dependencies
└── README.md                 # This documentation file
```

---

## License

MIT
