import os
import json
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API with the key from .env
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "automations_catalog.json")


def get_all_automations() -> list:
    """Load and return all automations from the JSON catalog."""
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading catalog: {e}")
        return []


def find_automation_by_id(automation_id: str) -> dict:
    """Find and return an automation entry by its ID, or None if not found."""
    automations = get_all_automations()
    for item in automations:
        if item.get("id") == automation_id:
            return item
    return None


def detect_automation(user_prompt: str) -> str:
    """
    Sends the user prompt and catalog metadata to Gemini.
    Returns the matched automation ID, or None if no match is found.
    """
    try:
        if not api_key:
            return None

        automations = get_all_automations()
        if not automations:
            return None

        # Build schema context for the model
        catalog_summary = []
        valid_ids = []
        for item in automations:
            aid = item.get("id")
            valid_ids.append(aid)
            catalog_summary.append(
                f"ID: {aid}\n"
                f"Name: {item.get('name')}\n"
                f"Description: {item.get('description')}\n"
                f"Keywords: {', '.join(item.get('keywords', []))}\n"
                f"---"
            )

        catalog_text = "\n".join(catalog_summary)

        # Structure instruction prompt precisely as requested
        system_instruction = (
            "You are a routing system. Match user intent to the correct automation ID from the provided catalog. "
            "Return ONLY the automation id that best matches this prompt. "
            "If nothing matches with reasonable confidence, return the word NONE. No explanation."
        )

        model_prompt = (
            f"Catalog:\n{catalog_text}\n\n"
            f"User Prompt: \"{user_prompt}\"\n\n"
            f"Match the prompt to an automation ID. "
            f"Return ONLY the automation id that best matches this prompt. If nothing matches with reasonable confidence, return the word NONE. No explanation."
        )

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_instruction,
        )

        # High confidence match requested, low temperature
        config = genai.types.GenerationConfig(temperature=0.1)
        response = model.generate_content(model_prompt, generation_config=config)
        
        detected_id = response.text.strip()
        if detected_id == "NONE" or detected_id not in valid_ids:
            return None

        return detected_id

    except Exception as e:
        print(f"Error detecting automation: {e}")
        return None


def simulate_execution(automation_id: str, input_values: dict) -> str:
    """
    Simulates local execution of a matched automation using provided inputs.
    Returns a formatted log showing execution steps, outputs and status.
    """
    automation = find_automation_by_id(automation_id)
    if not automation:
        return f"Error: Automation '{automation_id}' not found in catalog."

    name = automation.get("name")
    expected_outputs = automation.get("expected_outputs", [])

    # Retrieve inputs with fallbacks
    def get_val(key, default="[Unknown Value]"):
        val = input_values.get(key, "").strip()
        return val if val else default

    # Custom execution steps per automation id
    steps = []
    output_dummies = {}

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if automation_id == "employee_onboarding":
        full_name = get_val("full_name", "Jane Doe")
        email = get_val("email", "jane.doe@company.com")
        dept = get_val("department", "IT")
        join_date = get_val("joining_date", now_str.split(" ")[0])
        # Generate a dynamic Employee ID during execution
        emp_id = f"EMP-2026-{datetime.now().strftime('%M%S')}"

        steps = [
            f"Verifying employee ID '{emp_id}' validation and department checks.",
            f"Creating Active Directory user profile matching '{full_name}' ({email}).",
            f"Assigning AD user account permission flags to department security groups: '{dept}'.",
            f"Assembling orientation onboarding kit documents.",
            f"Dispatching onboarding orientation welcome notification packet to '{email}'."
        ]
        output_dummies = {
            "Active Directory Account provisioned": f"SUCCESS - User '{email}' created with ID '{emp_id}'",
            "Welcome onboarding email sent to new hire": f"SENT - Onboarding guidelines successfully sent to '{email}'",
            "Orientation schedule calendar invite generated": f"SCHEDULED - Session invite sent for {join_date}"
        }

    elif automation_id == "hr_training_invitation":
        recipients = get_val("recipient_emails", "training-attendee@company.com")
        title = get_val("training_title", "General Training Session")
        t_date = get_val("training_date", now_str.split(" ")[0])
        t_time = get_val("training_time", "11:00 AM")
        loc = get_val("location_or_link", "https://meet.google.com/abc-xyz")

        steps = [
            f"Parsing target training registration list from input text field.",
            f"Building training calendar invitation schedule details for '{title}' ({t_date} at {t_time}).",
            f"Connecting to corporate email distribution server.",
            f"Dispatching webinar invitations and calendar invitations to: '{recipients}'.",
            f"Creating entry logs inside training database metrics."
        ]
        output_dummies = {
            "Bulk email invitations sent to all recipients": f"SUCCESS - Dispatched to emails matching: {recipients}",
            "Calendar invites sent and synced": f"SUCCESS - Event sync to resource calendar created with location: {loc}",
            "Training attendance tracking log initialized": f"SUCCESS - DB table log initialized for training session: {title}"
        }

    elif automation_id == "leave_approval_notification":
        email = get_val("employee_email", "employee@company.com")
        name = get_val("employee_name", "Alex Mercer")
        start = get_val("leave_start_date", now_str.split(" ")[0])
        end = get_val("leave_end_date", now_str.split(" ")[0])
        approver = get_val("approved_by", "Supervisor")

        steps = [
            f"Retrieving company leave tracking database records.",
            f"Locating corresponding time-off record matching employee '{name}' ({email}).",
            f"Approving request in system and updating record status to 'Approved' by '{approver}'.",
            f"Dispatching leave request resolution email notifications to employee email '{email}'.",
            f"Broadcasting leave status update alert message to department channel."
        ]
        output_dummies = {
            "Leave approval notification email sent to employee": f"SENT - Email approval notice delivered to '{email}'",
            "HR Leave tracker DB updated with status 'Approved'": f"SUCCESS - Time off approved from {start} to {end}",
            "Slack/Teams notification sent to department channel": f"POSTED - Broadcasted leave of absence alert to channel"
        }

    elif automation_id == "invoice_processing":
        vendor = get_val("vendor_name", "Global Vendor")
        inv_num = get_val("invoice_number", "INV-1002")
        amount = get_val("amount", "100.00")
        due = get_val("due_date", now_str.split(" ")[0])
        dept = get_val("department", "Operations")

        steps = [
            f"Connecting to accounting ERP ledger endpoint matching department group: '{dept}'.",
            f"Extracting billing details for invoice '{inv_num}' from vendor account '{vendor}'.",
            f"Performing validation check of invoice sum of ${amount} against department budget caps.",
            f"Entering invoice record entry under accounting ledger database values.",
            f"Generating ERP transaction reference voucher details for transaction auditing."
        ]
        output_dummies = {
            "Invoice registered in ERP ledger": f"SUCCESS - Invoice '{inv_num}' logged with amount ${amount}",
            "Payment voucher generated for Finance": f"SUCCESS - Voucher V-ID {datetime.now().strftime('%j%H%M')} compiled",
            "Confirmation slip emailed to vendor": f"SENT - Log receipt dispatched to '{vendor}'"
        }

    elif automation_id == "new_user_account_creation":
        full_name = get_val("full_name", "Bruce Wayne")
        email = get_val("email", "bwayne@company.com")
        role = get_val("role", "Employee")
        dept = get_val("department", "Finance")

        steps = [
            f"Accessing centralized identity provider server credentials directory.",
            f"Creating fresh user entry for '{full_name}' under department role: '{dept}/{role}'.",
            f"Assigning user credentials permissions matching security group standard policies.",
            f"Generating secure temporary system login authorization credentials.",
            f"Dispatching encrypted initialization parameters pack to: '{email}'."
        ]
        output_dummies = {
            "User profile created in identity database": f"SUCCESS - Account linked for user '{full_name}'",
            "Security groups and permission roles assigned": f"SUCCESS - Permissions configured matching policies for: {role}",
            "Temporary credentials securely transmitted to employee": f"SENT - Instructions delivered to: {email}"
        }

    elif automation_id == "offboarding_workflow":
        name = get_val("employee_name", "Harvey Dent")
        email = get_val("employee_email", "hdent@company.com")
        last_date = get_val("last_working_date", now_str.split(" ")[0])
        manager = get_val("manager_email", "manager@company.com")

        steps = [
            f"Retrieving system HR employee termination offboarding tasks queue.",
            f"Scheduling identity access revocation protocols for '{name}' ({email}) effective '{last_date}'.",
            f"Creating physical hardware assets returns ticket in IT Service Desk database.",
            f"Drafting and sending exit checklist review questionnaire survey to '{email}'.",
            f"Sending status update verification email report to supervisor '{manager}'."
        ]
        output_dummies = {
            "Account access termination scheduled": f"SUCCESS - Access revocation schedule set for {last_date}",
            "Asset recovery ticket generated in IT Service Desk": f"SUCCESS - Recovery ticket created in system queue",
            "Offboarding exit survey link sent to employee": f"SENT - Survey link dispatched successfully to '{email}'"
        }

    elif automation_id == "payslip_distribution":
        month = get_val("month", "June")
        year = get_val("year", "2026")
        dept = get_val("department", "All")

        steps = [
            f"Accessing payroll database ledger for reporting time cycle: '{month} {year}'.",
            f"Compiling payment records for all active personnel under department group: '{dept}'.",
            f"Generating secure encrypted salary payslip documentation PDFs.",
            f"Establishing secure mail transmission gateway connection.",
            f"Distributing payslip notifications to employee inbox targets.",
            f"Creating and archiving salary ledger transaction logs."
        ]
        output_dummies = {
            "Encrypted PDF payslips generated from payroll database": f"SUCCESS - PDF assets compiled for {month} {year}",
            "Individual emails sent to employees with password protection": f"SUCCESS - Dispatched securely to department '{dept}'",
            "Delivery status audit log archived": f"SUCCESS - Audit ledger generated successfully"
        }

    elif automation_id == "compliance_report_generation":
        rep_type = get_val("report_type", "Quarterly")
        period = get_val("period", "Q2-2026")
        email = get_val("recipient_email", "audit@company.com")

        steps = [
            f"Gathering compliance logs from target servers matching period cycle: '{period}'.",
            f"Aggregating system regulatory metrics and audit details data.",
            f"Compiling compiled results in digital PDF compliance digest ({rep_type}).",
            f"Establishing secure connection to compliance vault backend.",
            f"Emailing compliance report digest matching targets to: '{email}'."
        ]
        output_dummies = {
            "Aggregate compliance metric calculations completed": f"SUCCESS - Compiled data metrics for {period}",
            "PDF compliance report generated with digital signature": f"SUCCESS - PDF report generated successfully",
            "Emailed report to compliance officer and stored in security vault": f"SENT - Dispatched to '{email}' and logged in vault"
        }

    elif automation_id == "asset_assignment":
        name = get_val("employee_name", "Diana Prince")
        email = get_val("employee_email", "diana@company.com")
        asset_type = get_val("asset_type", "Laptop")
        asset_id = get_val("asset_id", "AST-LAP-909")

        steps = [
            f"Connecting to corporate hardware inventory database systems.",
            f"Validating hardware status and availability for asset ID '{asset_id}' ({asset_type}).",
            f"Updating asset ownership tracking parameters to employee '{name}' ({email}).",
            f"Dispatching asset custody electronic signature request document link.",
            f"Logging assignment confirmation slip entry under IT support desk data logs."
        ]
        output_dummies = {
            "Inventory database updated with employee ownership assignment": f"SUCCESS - Asset '{asset_id}' mapped to '{name}'",
            "Asset custody policy signature request dispatched via DocuSign": f"SENT - Document request sent to '{email}'",
            "Log confirmation emailed to IT support desk": f"SUCCESS - Ticket confirmation logged"
        }

    elif automation_id == "password_reset_notification":
        email = get_val("employee_email", "user@company.com")
        name = get_val("employee_name", "Peter Parker")
        system = get_val("system_name", "VPN")

        steps = [
            f"Checking directory for active system login account records matching: '{name}' ({email}).",
            f"Creating temporary single-use password authorization reset token for system '{system}'.",
            f"Compiling secure password reset guide and token link guidelines.",
            f"Dispatching guide instructions notification email to employee target '{email}'.",
            f"Logging reset request audit credentials trail entry in directory history database."
        ]
        output_dummies = {
            "Password reset token generated": f"SUCCESS - Token generated: {datetime.now().strftime('%s%f') if hasattr(datetime.now(), 'strftime') else '17283949'}",
            "Secure reset instructions email dispatched to employee": f"SENT - Notification link dispatched to '{email}'",
            "Security audit trail record logged in AD directory logs": f"SUCCESS - Reset logged under target system '{system}'"
        }

    # Generate output text
    lines = []
    lines.append("==================================================================")
    lines.append(f"AUTOMATION TRIGGERED: {name}")
    lines.append("==================================================================")
    lines.append(f"Timestamp: {now_str}")
    lines.append("Status:    SUCCESS")
    lines.append("")
    lines.append("[INPUTS RECEIVED]")
    for k, v in input_values.items():
        # Clean label matching input key
        label = k.replace("_", " ").title()
        lines.append(f"  • {label}: {v}")
    lines.append("")
    lines.append("[STEPS EXECUTED]")
    for idx, step in enumerate(steps, 1):
        lines.append(f"  {idx}. {step}")
    lines.append("")
    lines.append("[OUTPUTS GENERATED]")
    for out in expected_outputs:
        dummy = output_dummies.get(out, "[Simulation Output Generated]")
        lines.append(f"  • {out}:")
        lines.append(f"    -> {dummy}")
    lines.append("==================================================================")

    return "\n".join(lines)
