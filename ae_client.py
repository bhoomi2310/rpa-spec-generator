import re
import requests
import base64
import time
import urllib3
from datetime import datetime
from ae_config import (
    AE_BASE_URL,
    AE_ORG_CODE,
    AE_CLIENT_ID,
    AE_CLIENT_SECRET
)
from error_logger import log_info, log_success, log_error

# Disable SSL verification warning messages for corporate networks
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Token cache
_token_cache = {"token": None, "expires_at": 0}

def get_session_token() -> str:
    import time
    if _token_cache["token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["token"]
    
    url = f"{AE_BASE_URL}/rest/appuser/oauth/v1/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": AE_CLIENT_ID,
        "client_secret": AE_CLIENT_SECRET
    }
    
    try:
        response = requests.post(url, data=data, verify=False, timeout=15)
        print(f"DEBUG: Token endpoint response: {response.status_code}")
        print(f"DEBUG: Response: {response.text[:300]}")
        
        if response.status_code == 200:
            result = response.json()
            token = (result.get("access_token") or
                     result.get("token") or
                     result.get("sessionToken") or
                     result.get("accessToken"))
            if token:
                _token_cache["token"] = token
                _token_cache["expires_at"] = time.time() + (8 * 3600)
                return token
        
        raise Exception(f"Token request failed: {response.status_code} {response.text[:200]}")
    except Exception as e:
        raise Exception(f"AutomationEdge auth failed: {str(e)}")

def fetch_workflows(session_token: str) -> list:
    """
    Fetches all workflows for the tenant and normalizes them.
    Supports array responses or dictionary responses containing keys like "data" or "workflows".
    """
    if not AE_BASE_URL:
        raise Exception("AE_BASE_URL is not set.")

    url = f"{AE_BASE_URL.rstrip('/')}/rest/tenants/{AE_ORG_CODE}/workflows"
    headers = {
        "Content-Type": "application/json",
        "X-session-token": session_token,
        "Authorization": f"Bearer {session_token}"
    }

    log_info(f"Fetching workflows from {url}")

    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        
        res_data = response.json()
        
        # Handle response format exceptions
        if isinstance(res_data, list):
            workflows = res_data
        elif isinstance(res_data, dict):
            workflows = res_data.get("workflows") or res_data.get("data") or res_data.get("workflowList") or res_data.get("list") or []
            if not isinstance(workflows, list):
                workflows = []
        else:
            workflows = []
        
        normalized = []
        for workflow in workflows:
            if not isinstance(workflow, dict):
                continue
            details = workflow.get("workflowConfigurationDetails")
            params = details.get("params") if details else None
            
            required_inputs = parse_params(params) if params else []
            wname = workflow.get("name", "Unnamed Workflow")
            wdesc = workflow.get("description") or ""
            
            normalized.append({
                "id": str(workflow.get("id", "")),
                "name": wname,
                "description": wdesc,
                "last_updated": workflow.get("lastUpdatedDate", 0),
                "keywords": extract_keywords(wname, wdesc),
                "required_inputs": required_inputs,
                "expected_outputs": infer_expected_outputs(wname, wdesc, params or []),
                "agentic_type": detect_agentic_type(wname, wdesc, params or [])
            })
        log_success(f"Fetched {len(workflows)} workflows")
        return normalized
    except Exception as e:
        log_error("Failed to fetch workflows", e)
        raise

def fetch_workflow_by_id(session_token: str, workflow_id: str) -> dict:
    """
    Fetches a single workflow by ID and returns its normalized structure.
    """
    if not AE_BASE_URL:
        raise Exception("AE_BASE_URL is not set.")

    url = f"{AE_BASE_URL.rstrip('/')}/rest/workflows/{workflow_id}"
    headers = {
        "Content-Type": "application/json",
        "X-session-token": session_token,
        "Authorization": f"Bearer {session_token}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        res_data = response.json()
        
        # Handle single workflow response structure
        if isinstance(res_data, dict):
            workflow = res_data.get("workflow") or res_data.get("data") or res_data
        else:
            workflow = res_data
            
        if not isinstance(workflow, dict):
            raise Exception("Single workflow response is not a JSON object.")

        details = workflow.get("workflowConfigurationDetails")
        params = details.get("params") if details else None
        required_inputs = parse_params(params) if params else []
        wname = workflow.get("name", "Unnamed Workflow")
        wdesc = workflow.get("description") or ""
        
        return {
            "id": str(workflow.get("id", "")),
            "name": wname,
            "description": wdesc,
            "last_updated": workflow.get("lastUpdatedDate", 0),
            "keywords": extract_keywords(wname, wdesc),
            "required_inputs": required_inputs,
            "expected_outputs": infer_expected_outputs(wname, wdesc, params or []),
            "agentic_type": detect_agentic_type(wname, wdesc, params or [])
        }
    except Exception as e:
        print(f"Warning: Failed to fetch workflow by ID {workflow_id}: {e}")
        raise

def get_latest_update_timestamp(session_token: str) -> int:
    """
    Fetches workflows to find the highest lastUpdatedDate timestamp.
    Returns 0 if the request fails.
    """
    if not AE_BASE_URL:
        return 0

    url = f"{AE_BASE_URL.rstrip('/')}/rest/tenants/{AE_ORG_CODE}/workflows"
    headers = {
        "Content-Type": "application/json",
        "X-session-token": session_token,
        "Authorization": f"Bearer {session_token}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        res_data = response.json()
        
        if isinstance(res_data, list):
            workflows = res_data
        elif isinstance(res_data, dict):
            workflows = res_data.get("workflows") or res_data.get("data") or res_data.get("workflowList") or res_data.get("list") or []
            if not isinstance(workflows, list):
                workflows = []
        else:
            workflows = []
            
        if not workflows:
            return 0
        
        timestamps = [
            wf.get("lastUpdatedDate", 0)
            for wf in workflows
            if isinstance(wf, dict) and wf.get("lastUpdatedDate") is not None
        ]
        return max(timestamps) if timestamps else 0
    except Exception as e:
        print(f"Warning: Failed to get latest update timestamp: {e}")
        return 0

def execute_workflow(session_token: str, workflow: dict, input_values: dict) -> dict:
    """
    Submits a workflow execution request to AutomationEdge API.
    """
    if not AE_BASE_URL:
        return {"success": False, "error": "AE_BASE_URL is not set.", "message": "Execution failed"}

    url = f"{AE_BASE_URL.rstrip('/')}/rest/tenants/{AE_ORG_CODE}/processes/requests"
    headers = {
        "Content-Type": "application/json",
        "X-session-token": session_token,
        "Authorization": f"Bearer {session_token}"
    }
    
    timestamp = int(datetime.now().timestamp())
    source_id = f"RPA-{timestamp}"
    
    params = []
    for index, item in enumerate(workflow.get("required_inputs", [])):
        params.append({
            "name": item["field"],
            "value": input_values.get(item["field"], ""),
            "type": None,
            "order": index + 1,
            "secret": item.get("secret", False),
            "optional": item.get("optional", False),
            "defaultValue": None,
            "displayName": item.get("label", item["field"]),
            "extension": None
        })
        
    body = {
        "orgCode": AE_ORG_CODE,
        "workflowName": workflow.get("name"),
        "source": "RPA Spec Generator",
        "sourceId": source_id,
        "userId": None,
        "responseMailSubject": None,
        "maxExecutionTimeInSeconds": None,
        "expectedExecutionTimeInSeconds": None,
        "params": params
    }
    
    log_info(f"Executing workflow: {workflow['name']}")

    try:
        response = requests.post(url, json=body, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        res_data = response.json()
        if isinstance(res_data, dict):
            if "success" not in res_data:
                res_data["success"] = True
            log_success(f"Workflow submitted: {res_data}")
            return res_data
        
        success_res = {"success": True, "response": res_data}
        log_success(f"Workflow submitted: {success_res}")
        return success_res
    except Exception as e:
        log_error("Workflow execution failed", e)
        return {"success": False, "error": str(e), "message": "Execution failed"}

def get_execution_status(session_token: str, request_id: str) -> dict:
    """
    Fetches the execution status of a submitted request.
    """
    if not AE_BASE_URL:
        return {"success": False, "error": "AE_BASE_URL is not set."}

    url = f"{AE_BASE_URL.rstrip('/')}/rest/tenants/{AE_ORG_CODE}/processes/requests/{request_id}"
    headers = {
        "X-session-token": session_token,
        "Authorization": f"Bearer {session_token}"
    }
    
    log_info(f"Checking status for request: {request_id}")

    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        res_data = response.json()
        if isinstance(res_data, dict):
            if "success" not in res_data:
                res_data["success"] = True
            return res_data
        return {"success": True, "response": res_data}
    except Exception as e:
        log_error("Status check failed", e)
        return {"success": False, "error": str(e)}

# =====================================================================
# RESPONSE PARSING — adjust here if API shape changes
# =====================================================================

def infer_expected_outputs(name: str, description: str, params: list) -> list:
    name_lower = (name + " " + (description or "")).lower()
    outputs = []
    
    if any(w in name_lower for w in ["email", "mail", "invite", "invitation", "notification", "notify"]):
        outputs.append("Email sent to recipient(s) successfully")
    if any(w in name_lower for w in ["onboard", "provision", "account", "user", "create"]):
        outputs.append("User account provisioned in target system")
    if any(w in name_lower for w in ["report", "compliance", "audit", "summary"]):
        outputs.append("Report generated and delivered")
    if any(w in name_lower for w in ["invoice", "payment", "finance", "payslip", "salary"]):
        outputs.append("Financial record created and logged")
    if any(w in name_lower for w in ["asset", "assign", "laptop", "device", "equipment"]):
        outputs.append("Asset assigned and inventory updated")
    if any(w in name_lower for w in ["offboard", "exit", "leaving", "resign", "terminate"]):
        outputs.append("Offboarding tasks completed across systems")
    if any(w in name_lower for w in ["password", "reset", "access", "credential"]):
        outputs.append("Password reset instructions sent")
    if any(w in name_lower for w in ["leave", "approval", "approve"]):
        outputs.append("Approval notification sent to employee")
    if any(w in name_lower for w in ["train", "hr", "learning", "course", "workshop"]):
        outputs.append("Training invitation sent to participants")
    if any(w in name_lower for w in ["agent", "ai", "llm", "classify", "summarize", "extract"]):
        outputs.append("AI processing completed — response generated")
        outputs.append("Token usage logged")
    
    if not outputs:
        outputs.append(f"Workflow '{name}' executed successfully")
        outputs.append("Execution log saved")
    
    outputs.append("Execution status updated in AutomationEdge")
    return outputs

def detect_agentic_type(name: str, description: str, params: list) -> str or None:
    text = (name + " " + (description or "")).lower()
    param_names = " ".join([p.get("name","") + " " + p.get("displayName","") 
                            for p in params]).lower()
    combined = text + " " + param_names
    
    if any(w in combined for w in ["classifier", "classify", "categorize", "category"]):
        return "Classifier"
    if any(w in combined for w in ["summarizer", "summarize", "summary", "condense"]):
        return "Summarizer"
    if any(w in combined for w in ["knowledge base", "knowledgebase", "knowledge_base", "km service"]):
        return "Knowledge Base"
    if any(w in combined for w in ["llm", "language model", "gpt", "gemini", "openai", "bedrock", "vertex"]):
        return "LLM"
    if any(w in combined for w in ["ai agent", "agentic", "agent", "mcp", "orchestrat"]):
        return "AI Agent"
    return None

def extract_keywords(name: str, description: str) -> list:
    """
    Extracts lowercase alphanumeric keywords from a name and description.
    Skips keywords shorter than 3 characters.
    """
    combined = f"{name} {description}".lower()
    words = re.findall(r'[a-zA-Z0-9]+', combined)
    filtered = [w for w in words if len(w) >= 3]
    return list(dict.fromkeys(filtered))

def parse_params(params_list) -> list:
    """
    Parses and normalizes the workflow parameters returned from AutomationEdge.
    """
    if not params_list:
        return []

    parsed = []
    sorted_params = sorted(params_list, key=lambda p: p.get("order", 0))

    for param in sorted_params:
        is_secret = param.get("secret", False)
        param_type = "password" if is_secret else "text"
        
        parsed.append({
            "field": param.get("name", ""),
            "label": param.get("displayName") or param.get("name", ""),
            "type": param_type,
            "placeholder": str(param.get("defaultValue") or param.get("value") or ""),
            "optional": param.get("optional", False),
            "secret": is_secret
        })
    return parsed
