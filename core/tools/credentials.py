"""JagX secure credential vault.

Passwords are stored in the operating-system credential store through keyring.
JagX may retrieve a secret for an authorized local tool flow, but the agent
sanitizes the result before it reaches the language model conversation.
"""
from __future__ import annotations

import getpass

try:
    import keyring
    HAS_KEYRING = True
except Exception:
    HAS_KEYRING = False

SERVICE = "JagX"


def request_password(account: str, reason: str = "authentication") -> str:
    """Ask locally for a password with hidden input; never write it to memory."""
    try:
        value = getpass.getpass(f"JagX needs the password for {account} ({reason}). Enter it (hidden): ")
        return value if value else "PASSWORD_INPUT_EMPTY"
    except Exception as e:
        return f"PASSWORD_INPUT_ERROR: {e}"


def save_credential(account: str, password: str) -> str:
    """Save a password in the OS credential store."""
    if not HAS_KEYRING:
        return "Secure credential storage is unavailable; install the keyring package first."
    if not account or not password:
        return "Credential was not saved: account and password are required."
    try:
        keyring.set_password(SERVICE, account.strip(), password)
        return f"Credential for {account.strip()} saved in the OS credential store."
    except Exception as e:
        return f"Could not save credential securely: {e}"


def get_credential(account: str) -> str:
    """Retrieve a stored password for an authorized local tool flow.

    The agent replaces the returned secret before sending the tool result to
    the LLM. This function should be used by local automation, not for chat
    display or logging.
    """
    if not HAS_KEYRING:
        return "SECURE_CREDENTIAL_ERROR: keyring unavailable"
    try:
        value = keyring.get_password(SERVICE, account.strip())
        if value is None:
            return "SECURE_CREDENTIAL_NOT_FOUND"
        return "SECURE_CREDENTIAL:" + value
    except Exception as e:
        return f"SECURE_CREDENTIAL_ERROR: {e}"


def has_credential(account: str) -> str:
    if not HAS_KEYRING:
        return "Secure credential storage unavailable."
    try:
        return "A credential is stored for this account." if keyring.get_password(SERVICE, account.strip()) else "No credential is stored for this account."
    except Exception as e:
        return f"Credential-store error: {e}"


def delete_credential(account: str) -> str:
    """Delete one stored credential from the OS credential store."""
    if not HAS_KEYRING:
        return "Secure credential storage unavailable."
    try:
        keyring.delete_password(SERVICE, account.strip())
        return f"Credential for {account.strip()} deleted from the OS credential store."
    except keyring.errors.PasswordDeleteError:
        return "No stored credential was found for that account."
    except Exception as e:
        return f"Credential-store error: {e}"


def list_credential_accounts() -> str:
    """Return only locally configured account labels, never passwords."""
    return "Credential account discovery is intentionally disabled because the OS credential manager does not provide a safe portable listing API. Use has_credential(account) when you know the account label."


CREDENTIAL_TOOLS = [
    {"type":"function","function":{"name":"request_password","description":"Ask the user to enter a password locally with hidden input. Never store or expose the password in model conversation.","parameters":{"type":"object","properties":{"account":{"type":"string"},"reason":{"type":"string","default":"authentication"}},"required":["account"]}}},
    {"type":"function","function":{"name":"save_credential","description":"Save a password into the operating system credential store after the user supplies it. Never put the password into model memory.","parameters":{"type":"object","properties":{"account":{"type":"string"},"password":{"type":"string"}},"required":["account","password"]}}},
    {"type":"function","function":{"name":"get_credential","description":"Retrieve a stored password for an authorized LOCAL tool flow. Never display, quote, log, remember, or repeat the secret to the user or language model.","parameters":{"type":"object","properties":{"account":{"type":"string"}},"required":["account"]}}},
    {"type":"function","function":{"name":"has_credential","description":"Check whether JagX has an OS-stored credential without revealing its secret.","parameters":{"type":"object","properties":{"account":{"type":"string"}},"required":["account"]}}},
    {"type":"function","function":{"name":"delete_credential","description":"Delete a stored credential from the OS credential store.","parameters":{"type":"object","properties":{"account":{"type":"string"}},"required":["account"]}}},
    {"type":"function","function":{"name":"list_credential_accounts","description":"Explain the safe credential-account discovery limitation without exposing secrets.","parameters":{"type":"object","properties":{}}}},
]

TOOL_FUNCTIONS = {
    "request_password": request_password,
    "save_credential": save_credential,
    "get_credential": get_credential,
    "has_credential": has_credential,
    "delete_credential": delete_credential,
    "list_credential_accounts": list_credential_accounts,
}
