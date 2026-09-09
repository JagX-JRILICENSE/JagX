"""JagX secure credential helper.
Passwords are handled through the OS credential store when keyring is available;
JagX never sends stored passwords to the language model.
"""
from __future__ import annotations

import getpass
import os

try:
    import keyring
    HAS_KEYRING = True
except Exception:
    HAS_KEYRING = False

SERVICE = "JagX"


def request_password(account: str, reason: str = "authentication") -> str:
    """Ask the user for a password without echoing it and return it only to the tool caller."""
    # This is deliberately a direct local prompt; the value is not written to memory or chat.
    try:
        return getpass.getpass(f"JagX needs the password for {account} ({reason}). Enter it (hidden): ")
    except Exception as e:
        return f"PASSWORD_INPUT_ERROR: {e}"


def save_credential(account: str, password: str) -> str:
    """Save a credential in the operating system credential store, if enabled."""
    if not HAS_KEYRING:
        return "Secure credential storage is unavailable; install the keyring package first."
    try:
        keyring.set_password(SERVICE, account, password)
        return f"Credential for {account} saved in the OS credential store."
    except Exception as e:
        return f"Could not save credential securely: {e}"


def has_credential(account: str) -> str:
    if not HAS_KEYRING:
        return "Secure credential storage unavailable."
    try:
        return "A credential is stored for this account." if keyring.get_password(SERVICE, account) else "No credential is stored for this account."
    except Exception as e:
        return f"Credential-store error: {e}"


CREDENTIAL_TOOLS = [
    {"type":"function","function":{"name":"request_password","description":"Ask the user to enter a password locally with hidden input. Never store or expose the password in the model conversation.","parameters":{"type":"object","properties":{"account":{"type":"string"},"reason":{"type":"string","default":"authentication"}},"required":["account"]}}},
    {"type":"function","function":{"name":"save_credential","description":"Save a password into the operating system credential store after the user has supplied it. Never put the password into model memory.","parameters":{"type":"object","properties":{"account":{"type":"string"},"password":{"type":"string"}},"required":["account","password"]}}},
    {"type":"function","function":{"name":"has_credential","description":"Check whether JagX has an OS-stored credential for an account without revealing its secret.","parameters":{"type":"object","properties":{"account":{"type":"string"}},"required":["account"]}}},
]

TOOL_FUNCTIONS = {"request_password": request_password, "save_credential": save_credential, "has_credential": has_credential}
