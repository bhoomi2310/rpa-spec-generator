import os
from datetime import datetime
from dotenv import load_dotenv
from google import genai

# Load environment variables from .env file
load_dotenv()

# Initialize the Gemini API client once per file
api_key = os.getenv("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)

# Module-level variable to store dynamically loaded mappings
LIVE_MAPPINGS = []

def initialize(mappings: list):
    """
    Sets the live mappings loaded from the cache or synced from the API.
    """
    global LIVE_MAPPINGS
    LIVE_MAPPINGS = mappings

def get_all_automations() -> list:
    """
    Returns the live workflows database list.
    """
    return LIVE_MAPPINGS

def find_automation_by_id(automation_id: str) -> dict:
    """
    Finds and returns a workflow entry by its ID, or None if not found.
    """
    for item in LIVE_MAPPINGS:
        if str(item.get("id")) == str(automation_id):
            return item
    return None

def detect_automation(user_prompt: str) -> str:
    """
    Sends the user prompt and live workflow mappings to Gemini to identify a match.
    Returns the matched automation ID, or None if no match is found.
    """
    try:
        if not api_key or not client:
            print("Warning: GEMINI_API_KEY is not set.")
            return None

        if not LIVE_MAPPINGS:
            return None

        # Format mappings into a simple text summary for the model context
        summary_list = []
        valid_ids = set()
        for item in LIVE_MAPPINGS:
            aid = str(item.get("id"))
            valid_ids.add(aid)
            keywords_str = ", ".join(item.get("keywords", []))
            summary_list.append(
                f"ID: {aid}\n"
                f"Name: {item.get('name')}\n"
                f"Description: {item.get('description') or ''}\n"
                f"Keywords: {keywords_str}"
            )
        
        automations_text = "\n\n".join(summary_list)

        # Build prompt exactly as requested by the specification
        model_prompt = (
            f"Given these automations:\n{automations_text}\n\n"
            f"Which automation id best matches this user request: '{user_prompt}'?\n"
            f"Reply with ONLY the automation id. If nothing matches, reply NONE."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=model_prompt,
            config={"temperature": 0.1}
        )
        
        detected_id = response.text.strip()
        if not detected_id or detected_id.upper() == "NONE" or detected_id not in valid_ids:
            return None

        return detected_id
    except Exception as e:
        print(f"Error detecting automation: {e}")
        return None

def detect_multiple_automations(user_prompt: str) -> list:
    """
    Sends the user prompt and live workflow mappings to Gemini to identify up to 3 matches.
    Returns a list of full matched workflow objects (empty list if NONE or parsing fails).
    """
    try:
        if not api_key or not client:
            print("Warning: GEMINI_API_KEY is not set.")
            return []

        if not LIVE_MAPPINGS:
            return []

        # Build list of id | name | description | keywords for each
        summary_list = []
        mapping_by_id = {}
        for item in LIVE_MAPPINGS:
            aid = str(item.get("id"))
            mapping_by_id[aid] = item
            keywords_str = ", ".join(item.get("keywords", []))
            summary_list.append(
                f"id: {aid} | name: {item.get('name')} | description: {item.get('description') or ''} | keywords: {keywords_str}"
            )
        
        automations_text = "\n".join(summary_list)

        # Build prompt exactly as requested by the specification
        model_prompt = (
            f"Given these automations (id | name | description | keywords):\n"
            f"{automations_text}\n\n"
            f"The user wants: '{user_prompt}'\n\n"
            f"Return the IDs of up to 3 automations that are most relevant, "
            f"ordered by relevance (best match first).\n"
            f"Return ONLY a comma-separated list of IDs with no spaces.\n"
            f"Example: employee_onboarding,hr_training_invitation\n"
            f"If nothing matches at all, return NONE."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=model_prompt,
            config={"temperature": 0.1}
        )
        
        response_text = response.text.strip()
        if not response_text or response_text.upper() == "NONE":
            return []

        # Parse comma-separated response into a list of id strings
        ids = [i.strip() for i in response_text.split(",") if i.strip()]
        
        # Look up each ID in LIVE_MAPPINGS and return full workflow objects
        results = []
        for aid in ids:
            if aid in mapping_by_id:
                results.append(mapping_by_id[aid])
                
        return results
    except Exception as e:
        print(f"Error detecting multiple automations: {e}")
        return []

def simulate_execution(automation_id: str, input_values: dict) -> str:
    """
    Simulates local execution of a matched automation and returns formatted log output.
    """
    automation = find_automation_by_id(automation_id)
    if not automation:
        return f"Error: Automation '{automation_id}' not found."

    name = automation.get("name", "Unknown Workflow")
    expected_outputs = automation.get("expected_outputs", [])
    agentic_type = automation.get("agentic_type")

    # Format inputs for log display
    inputs_lines = []
    for inp in automation.get("required_inputs", []):
        field = inp.get("field")
        label = inp.get("label") or field
        val = input_values.get(field, "").strip()
        
        # Redact password values in output logs
        if inp.get("type") == "password" and val:
            val_display = "••••••••"
        else:
            val_display = val if val else "[Empty]"
            
        inputs_lines.append(f"  • {label}: {val_display}")

    inputs_received_str = "\n".join(inputs_lines)

    # Format expected outputs
    outputs_lines = []
    for out in expected_outputs:
        outputs_lines.append(f"  • {out}")
    outputs_str = "\n".join(outputs_lines)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Construct steps executed
    steps = [
        "Validating inputs and establishing connection to AutomationEdge",
        f"Initializing workflow: {name}",
        "Processing inputs through workflow engine"
    ]
    if agentic_type:
        steps.extend([
            f"  → Agentic AI plugin initialized ({agentic_type} step)",
            "  → LLM provider connected and authenticated",
            "  → AI processing input data...",
            "  → Generating context-aware response",
            "  → AI step completed — output captured"
        ])
    steps.extend([
        "Executing configured actions on target systems",
        "Capturing output and generating execution log",
        "Workflow completed — awaiting confirmation"
    ])
    
    steps_formatted = []
    current_index = 1
    for step in steps:
        if step.strip().startswith("→"):
            steps_formatted.append(step)
        else:
            steps_formatted.append(f"  {current_index}. {step}")
            current_index += 1
    steps_str = "\n".join(steps_formatted)

    # Generate log layout adhering strictly to specification rules
    result = (
        f"✓ Automation: {name}\n"
        f"─────────────────────────\n"
        f"Inputs Received:\n"
        f"{inputs_received_str}\n\n"
        f"Steps Executed:\n"
        f"{steps_str}\n\n"
        f"Expected Outputs:\n"
        f"{outputs_str}\n\n"
        f"─────────────────────────\n"
        f"Status: SUCCESS (Simulated)\n"
        f"Timestamp: {now_str}\n"
        f"Note: Connect AutomationEdge credentials in .env to enable live execution"
    )

    return result
