"""JagX secure credential vault.

Secrets are stored in the operating-system credential store through keyring.
Passwords are collected locally with hidden input whenever possible and are
never intended to enter model conversation, logs, or GitHub.
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
    """Save a supplied password in the OS credential store.

    Prefer save_credential_interactive so the password never needs to be passed
    as a model tool argument.
    """
    if not HAS_KEYRING:
        return "Secure credential storage is unavailable; install the keyring package first."
    if not account or not password:
        return "Credential was not saved: account and password are required."
    try:
        keyring.set_password(SERVICE, account.strip(), password)
        return f"Credential for {account.strip()} saved in the OS credential store."
    except Exception as e:
        return f"Could not save credential securely: {e}"


def save_credential_interactive(account: str, reason: str = "credential setup") -> str:
    """Prompt locally for a password and save it without exposing it to the LLM."""
    if not HAS_KEYRING:
        return "Secure credential storage is unavailable; install the keyring package first."
    if not account:
        return "Credential was not saved: account is required."
    try:
        password = getpass.getpass(f"JagX — enter password for {account} ({reason}) (hidden): ")
        if not password:
            return "Credential was not saved: empty password."
        keyring.set_password(SERVICE, account.strip(), password)
        return f"Credential for {account.strip()} saved securely in the OS credential store."
    except Exception as e:
        return f"Could not save credential securely: {e}"


def get_credential(account: str) -> str:
    """Retrieve a stored password for an authorized LOCAL tool flow only."""
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
    return "Credential account discovery is intentionally disabled because the OS credential manager does not provide a safe portable listing API. Use has_credential(account) when you know the account label."


CREDENTIAL_TOOLS = [
    {"type":"function","function":{"name":"request_password","description":"Ask the user to enter a password locally with hidden input. Never store or expose the password in model conversation.","parameters":{"type":"object","properties":{"account":{"type":"string"},"reason":{"type":"string","default":"authentication"}},"required":["account"]}}},
    {"type":"function","function":{"name":"save_credential","description":"Save a password into the operating system credential store. Prefer save_credential_interactive so the secret is entered locally rather than passed through model arguments.","parameters":{"type":"object","properties":{"account":{"type":"string"},"password":{"type":"string"}},"required":["account","password"]}}},
    {"type":"function","function":{"name":"save_credential_interactive","description":"Securely prompt for a password locally with hidden input and save it to the OS credential store without returning the secret to the model.","parameters":{"type":"object","properties":{"account":{"type":"string"},"reason":{"type":"string","default":"credential setup"}},"required":["account"]}}},
    {"type":"function","function":{"name":"get_credential","description":"Retrieve a stored password for an authorized LOCAL tool flow. Never display, quote, log, remember, or repeat the secret to the user or language model.","parameters":{"type":"object","properties":{"account":{"type":"string"}},"required":["account"]}}},
    {"type":"function","function":{"name":"has_credential","description":"Check whether JagX has an OS-stored credential without revealing its secret.","parameters":{"type":"object","properties":{"account":{"type":"string"}},"required":["account"]}}},
    {"type":"function","function":{"name":"delete_credential","description":"Delete a stored credential from the OS credential store.","parameters":{"type":"object","properties":{"account":{"type":"string"}},"required":["account"]}}},
    {"type":"function","function":{"name":"list_credential_accounts","description":"Explain the safe credential-account discovery limitation without exposing secrets.","parameters":{"type":"object","properties":{}}}},
]

TOOL_FUNCTIONS = {name: globals()[name] for name in [
    "request_password", "save_credential", "save_credential_interactive", "get_credential",
    "has_credential", "delete_credential", "list_credential_accounts"
]}
