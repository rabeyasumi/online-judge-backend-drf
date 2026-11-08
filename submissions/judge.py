
import requests
from django.conf import settings

from .languages import LANGUAGES


JDOODLE_URL = "https://api.jdoodle.com/v1/execute"


class JudgeServiceError(Exception):
    pass


def execute_code(code, language, stdin="", compile_only=False):

    # 1. Find language configuration
    language_config = next(
        (
            item for item in LANGUAGES
            if item["language"] == language
        ),
        None
    )

    if language_config is None:
        raise JudgeServiceError("Unsupported programming language.")

    # 2. Check credentials
    client_id = settings.JDOODLE_CLIENT_ID
    client_secret = settings.JDOODLE_CLIENT_SECRET

    if not client_id or not client_secret:
        raise JudgeServiceError("JDoodle credentials are missing.")

    # 3. Prepare request
    payload = {
        "clientId": client_id,
        "clientSecret": client_secret,
        "script": code,
        "stdin": stdin,
        "language": language_config["language"],
        "versionIndex": language_config["version_index"],
        "compileOnly": compile_only,
    }

    # 4. Send request
    try:
        response = requests.post(
            JDOODLE_URL,
            json=payload,
            timeout=30
        )

    except requests.Timeout:
        raise JudgeServiceError("JDoodle request timed out.")

    except requests.RequestException:
        raise JudgeServiceError("Could not connect to JDoodle.")

    # 5. Read JSON response
    try:
        result = response.json()

    except ValueError:
        raise JudgeServiceError("Invalid response from JDoodle.")

    if not isinstance(result, dict):
        raise JudgeServiceError("Unexpected JDoodle response.")

    # 6. Handle HTTP errors
    if response.status_code == 401:
        raise JudgeServiceError("JDoodle credentials are invalid.")

    if response.status_code == 429:
        raise JudgeServiceError("JDoodle daily execution limit reached.")

    if response.status_code != 200:
        raise JudgeServiceError("JDoodle service request failed.")

    # 7. Handle JDoodle API errors
    if result.get("error"):
        raise JudgeServiceError(str(result["error"]))

    if result.get("statusCode") not in (None, 200):
        raise JudgeServiceError("JDoodle execution request failed.")

    # 8. Return execution information
    return {
        "output": result.get("output", ""),
        "execution_time": result.get("cpuTime"),
        "memory": result.get("memory"),
        "compilation_status": result.get("compilationStatus"),
    }
