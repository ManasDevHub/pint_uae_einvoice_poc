import httpx
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

async def validate_with_peppol_api(xml_payload: str | bytes) -> Dict[str, Any]:
    """
    Sends an XML payload to the Peppol Validator API.
    Returns the parsed JSON response.
    """
    url = "https://peppolvalidator.com/api/v1/validate"
    headers = {"Content-Type": "application/xml"}
    
    # Ensure payload is bytes if it's string, or decode if we need to format it in logs?
    content = xml_payload if isinstance(xml_payload, bytes) else xml_payload.encode('utf-8')
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, content=content, headers=headers)
            response.raise_for_status()
            
            # Expected JSON format:
            # {
            #    "status": "valid" | "invalid" | "error",
            #    "errors": [{"rule": "...", "message": "...", "location": "..."}],
            #    "warnings": [{"rule": "...", "message": "...", "location": "..."}],
            #    "metadata": {...}
            # }
            return response.json()
    except httpx.HTTPStatusError as exc:
        logger.error(f"HTTPStatusError from peppolvalidator: {exc.response.text}")
        return {
            "status": "error",
            "errors": [{"rule": "API_ERROR", "message": f"Validator API returned {exc.response.status_code}: {exc.response.text}", "location": "/"}],
            "warnings": []
        }
    except Exception as exc:
        logger.error(f"Error calling peppolvalidator: {exc}")
        return {
            "status": "error",
            "errors": [{"rule": "NETWORK_ERROR", "message": f"Failed to contact Validator API: {str(exc)}", "location": "/"}],
            "warnings": []
        }

def validate_with_peppol_api_sync(xml_payload: str | bytes) -> Dict[str, Any]:
    """
    Synchronous version of validate_with_peppol_api for use in Celery tasks.
    """
    url = "https://peppolvalidator.com/api/v1/validate"
    headers = {"Content-Type": "application/xml"}
    content = xml_payload if isinstance(xml_payload, bytes) else xml_payload.encode('utf-8')
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, content=content, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        logger.error(f"HTTPStatusError from peppolvalidator (sync): {exc.response.text}")
        return {
            "status": "error",
            "errors": [{"rule": "API_ERROR", "message": f"Validator API returned {exc.response.status_code}: {exc.response.text}", "location": "/"}],
            "warnings": []
        }
    except Exception as exc:
        logger.error(f"Error calling peppolvalidator (sync): {exc}")
        return {
            "status": "error",
            "errors": [{"rule": "NETWORK_ERROR", "message": f"Failed to contact Validator API: {str(exc)}", "location": "/"}],
            "warnings": []
        }

def map_peppol_to_internal_errors(peppol_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Maps the generic Peppol Validator response into the internal ValidationErrorItem format.
    """
    mapped_errors = []
    
    if not peppol_result:
        return mapped_errors

    # Map actual errors
    for err in peppol_result.get("errors", []):
        mapped_errors.append({
            "field": err.get("rule", "UNKNOWN_RULE"),
            "error": err.get("message", "No message provided"),
            "severity": "HIGH",
            "category": "COMPLIANCE"
        })
        
    return mapped_errors

def map_peppol_to_internal_warnings(peppol_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    mapped_warnings = []
    if not peppol_result:
        return mapped_warnings
        
    for w in peppol_result.get("warnings", []):
        mapped_warnings.append({
            "field": w.get("rule", "UNKNOWN_RULE"),
            "error": w.get("message", "No message provided"),
            "severity": "MEDIUM",
            "category": "COMPLIANCE"
        })
    return mapped_warnings
