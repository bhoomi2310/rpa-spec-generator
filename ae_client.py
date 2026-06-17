import re
import requests
import base64
import time
from datetime import datetime
from ae_config import (
    AE_BASE_URL,
    AE_ORG_CODE,
    AE_CLIENT_ID,
    AE_CLIENT_SECRET
)

# Token cache and startup debug print flag
_token_cache = {"token": None, "expires_at": 0.0}
_first_auth_run = True

def get_session_token() -> str:
    """
    Retrieves a cached OAuth2 access token, or requests a new one
    using 4 sequential OAuth2 client credential formats if expired/invalid.
    """
    global _token_cache, _first_auth_run

    now = time.time()
    if _token_cache.get("token") and now < _token_cache.get("expires_at", 0.0):
        return _token_cache["token"]

    if not AE_BASE_URL:
        raise Exception("AutomationEdge auth failed: AE_BASE_URL is not set.")
    if not AE_CLIENT_ID or not AE_CLIENT_SECRET:
        raise Exception("AutomationEdge auth failed: Client ID or Client Secret not set.")

    token_url = f"{AE_BASE_URL.rstrip('/')}/oauth/token"
    errors = []

    # FORMAT A — application/x-www-form-urlencoded body
    try:
        body = {
            "grant_type": "client_credentials",
            "client_id": AE_CLIENT_ID,
            "client_secret": AE_CLIENT_SECRET,
            "scope": "openid"
        }
        if _first_auth_run:
            print(f"DEBUG: Trying Format A POST to {token_url} with urlencoded body.")
        response = requests.post(
            token_url,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )
        if _first_auth_run:
            print(f"DEBUG: Format A Response Code: {response.status_code}")
            print(f"DEBUG: Format A Response Text: {response.text[:500]}")
            
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token") or data.get("token") or data.get("sessionToken") or data.get("sessiontoken")
            if token:
                expires_in = data.get("expires_in", 3600)
                _token_cache = {
                    "token": token,
                    "expires_at": time.time() + float(expires_in) - 60.0
                }
                _first_auth_run = False
                return token
        errors.append(f"Format A failed (status {response.status_code}): {response.text}")
    except Exception as e:
        errors.append(f"Format A failed with exception: {e}")

    # FORMAT B — JSON body
    try:
        body = {
            "grant_type": "client_credentials",
            "client_id": AE_CLIENT_ID,
            "client_secret": AE_CLIENT_SECRET,
            "scope": "openid"
        }
        if _first_auth_run:
            print(f"DEBUG: Trying Format B POST to {token_url} with JSON body.")
        response = requests.post(
            token_url,
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        if _first_auth_run:
            print(f"DEBUG: Format B Response Code: {response.status_code}")
            print(f"DEBUG: Format B Response Text: {response.text[:500]}")
            
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token") or data.get("token") or data.get("sessionToken") or data.get("sessiontoken")
            if token:
                expires_in = data.get("expires_in", 3600)
                _token_cache = {
                    "token": token,
                    "expires_at": time.time() + float(expires_in) - 60.0
                }
                _first_auth_run = False
                return token
        errors.append(f"Format B failed (status {response.status_code}): {response.text}")
    except Exception as e:
        errors.append(f"Format B failed with exception: {e}")

    # FORMAT C — HTTP Basic Auth header + Form body
    try:
        credentials = f"{AE_CLIENT_ID}:{AE_CLIENT_SECRET}"
        encoded_creds = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_creds}"
        }
        body = {
            "grant_type": "client_credentials",
            "scope": "openid"
        }
        if _first_auth_run:
            print(f"DEBUG: Trying Format C POST to {token_url} with Basic Auth header.")
        response = requests.post(
            token_url,
            data=body,
            headers=headers,
            timeout=15
        )
        if _first_auth_run:
            print(f"DEBUG: Format C Response Code: {response.status_code}")
            print(f"DEBUG: Format C Response Text: {response.text[:500]}")
            
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token") or data.get("token") or data.get("sessionToken") or data.get("sessiontoken")
            if token:
                expires_in = data.get("expires_in", 3600)
                _token_cache = {
                    "token": token,
                    "expires_at": time.time() + float(expires_in) - 60.0
                }
                _first_auth_run = False
                return token
        errors.append(f"Format C failed (status {response.status_code}): {response.text}")
    except Exception as e:
        errors.append(f"Format C failed with exception: {e}")

    # FORMAT D — Org-scoped endpoints
    org_scoped_endpoints = [
        f"{AE_BASE_URL.rstrip('/')}/oauth/{AE_ORG_CODE}/token",
        f"{AE_BASE_URL.rstrip('/')}/rest/auth/{AE_ORG_CODE}/oauth/token",
        f"{AE_BASE_URL.rstrip('/')}/rest/{AE_ORG_CODE}/oauth/token",
        f"{AE_BASE_URL.rstrip('/')}/oauth/token/{AE_ORG_CODE}",
    ]
    for endpoint in org_scoped_endpoints:
        try:
            body = {
                "grant_type": "client_credentials",
                "client_id": AE_CLIENT_ID,
                "client_secret": AE_CLIENT_SECRET,
                "scope": "openid"
            }
            if _first_auth_run:
                print(f"DEBUG: Trying Format D POST to {endpoint} with urlencoded body.")
            response = requests.post(
                endpoint,
                data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15
            )
            if _first_auth_run:
                print(f"DEBUG: Format D ({endpoint}) Response Code: {response.status_code}")
                print(f"DEBUG: Format D ({endpoint}) Response Text: {response.text[:500]}")
                
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token") or data.get("token") or data.get("sessionToken") or data.get("sessiontoken")
                if token:
                    expires_in = data.get("expires_in", 3600)
                    _token_cache = {
                        "token": token,
                        "expires_at": time.time() + float(expires_in) - 60.0
                    }
                    _first_auth_run = False
                    return token
            errors.append(f"Format D ({endpoint}) failed (status {response.status_code}): {response.text}")
        except Exception as e:
            errors.append(f"Format D ({endpoint}) failed with exception: {e}")

    # If all failed:
    _first_auth_run = False
    combined_errors = "\n".join(errors)
    raise Exception(f"All 4 OAuth2 formats failed to retrieve a token:\n{combined_errors}")

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

    try:
        response = requests.get(url, headers=headers, timeout=15)
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
            
            normalized.append({
                "id": str(workflow.get("id", "")),
                "name": workflow.get("name", "Unnamed Workflow"),
                "description": workflow.get("description") or "",
                "last_updated": workflow.get("lastUpdatedDate", 0),
                "keywords": extract_keywords(workflow.get("name", ""), workflow.get("description") or ""),
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
        "X-session-token": session_token,
        "Authorization": f"Bearer {session_token}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
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
        
        return {
            "id": str(workflow.get("id", "")),
            "name": workflow.get("name", "Unnamed Workflow"),
            "description": workflow.get("description") or "",
            "last_updated": workflow.get("lastUpdatedDate", 0),
            "keywords": extract_keywords(workflow.get("name", ""), workflow.get("description") or ""),
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
        "X-session-token": session_token,
        "Authorization": f"Bearer {session_token}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
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
        "X-session-token": session_token,
        "Authorization": f"Bearer {session_token}"
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
