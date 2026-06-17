import re
import requests
from datetime import datetime
from ae_config import (
    AE_BASE_URL,
    AE_ORG_CODE,
    AE_USERNAME,
    AE_PASSWORD,
    AE_SESSION_TOKEN
)

def get_session_token() -> str:
    """
    Returns the session token.
    If AE_SESSION_TOKEN is pre-configured, returns it directly.
    Otherwise, authenticates via POST to /rest/auth/login.
    """
    if AE_SESSION_TOKEN:
        return AE_SESSION_TOKEN

    if not AE_BASE_URL:
        raise Exception("AutomationEdge login failed: AE_BASE_URL is not set.")

    url = f"{AE_BASE_URL.rstrip('/')}/rest/auth/login"
    body = {
        "orgCode": AE_ORG_CODE,
        "username": AE_USERNAME,
        "password": AE_PASSWORD
    }

    try:
        response = requests.post(url, json=body, timeout=15)
        if response.status_code != 200:
            raise Exception(f"AutomationEdge login failed: {response.status_code} {response.text}")
        
        data = response.json()
        token = data.get("sessionToken") or data.get("token") or data.get("sessiontoken")
        if not token:
            raise Exception("No session token key ('sessionToken', 'token', or 'sessiontoken') found in login response.")
        
        return token
    except Exception as e:
        print(f"Warning: Login to AutomationEdge failed: {e}")
        raise

def fetch_workflows(session_token: str) -> list:
    """
    Fetches all workflows for the tenant and normalizes them.
    """
    if not AE_BASE_URL:
        raise Exception("AE_BASE_URL is not set.")

    url = f"{AE_BASE_URL.rstrip('/')}/rest/tenants/{AE_ORG_CODE}/workflows"
    headers = {
        "Content-Type": "application/json",
        "X-session-token": session_token
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        workflows = response.json()
        
        normalized = []
        for workflow in workflows:
            details = workflow.get("workflowConfigurationDetails")
            params = details.get("params") if details else None
            
            required_inputs = parse_params(params) if params else []
            
            normalized.append({
                "id": str(workflow["id"]),
                "name": workflow["name"],
                "description": workflow.get("description") or "",
                "last_updated": workflow.get("lastUpdatedDate", 0),
                "keywords": extract_keywords(workflow["name"], workflow.get("description") or ""),
                "required_inputs": required_inputs,
                "expected_outputs": [
                    "Workflow executed successfully",
                    "Execution log generated",
                    "Status report created"
                ]
            })
        return normalized
    except Exception as e:
        print(f"Warning: Failed to fetch workflows: {e}")
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
        "X-session-token": session_token
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        workflow = response.json()
        
        details = workflow.get("workflowConfigurationDetails")
        params = details.get("params") if details else None
        required_inputs = parse_params(params) if params else []
        
        return {
            "id": str(workflow["id"]),
            "name": workflow["name"],
            "description": workflow.get("description") or "",
            "last_updated": workflow.get("lastUpdatedDate", 0),
            "keywords": extract_keywords(workflow["name"], workflow.get("description") or ""),
            "required_inputs": required_inputs,
            "expected_outputs": [
                "Workflow executed successfully",
                "Execution log generated",
                "Status report created"
            ]
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
        "X-session-token": session_token
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        workflows = response.json()
        if not workflows or not isinstance(workflows, list):
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
        "X-session-token": session_token
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
        "userId": AE_USERNAME,
        "responseMailSubject": None,
        "maxExecutionTimeInSeconds": None,
        "expectedExecutionTimeInSeconds": None,
        "params": params
    }
    
    try:
        response = requests.post(url, json=body, headers=headers, timeout=15)
        response.raise_for_status()
        res_data = response.json()
        if isinstance(res_data, dict):
            if "success" not in res_data:
                res_data["success"] = True
            return res_data
        return {"success": True, "response": res_data}
    except Exception as e:
        print(f"Warning: Workflow execution request failed: {e}")
        return {"success": False, "error": str(e), "message": "Execution failed"}

def get_execution_status(session_token: str, request_id: str) -> dict:
    """
    Fetches the execution status of a submitted request.
    """
    if not AE_BASE_URL:
        return {"success": False, "error": "AE_BASE_URL is not set."}

    url = f"{AE_BASE_URL.rstrip('/')}/rest/tenants/{AE_ORG_CODE}/processes/requests/{request_id}"
    headers = {
        "X-session-token": session_token
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        res_data = response.json()
        if isinstance(res_data, dict):
            if "success" not in res_data:
                res_data["success"] = True
            return res_data
        return {"success": True, "response": res_data}
    except Exception as e:
        print(f"Warning: Failed to fetch execution status for request {request_id}: {e}")
        return {"success": False, "error": str(e)}

# =====================================================================
# RESPONSE PARSING — adjust here if API shape changes
# =====================================================================

def extract_keywords(name: str, description: str) -> list:
    """
    Extracts lowercase alphanumeric keywords from a name and description.
    """
    combined = f"{name} {description}".lower()
    words = re.findall(r'[a-zA-Z0-9]+', combined)
    return list(dict.fromkeys(words))

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
