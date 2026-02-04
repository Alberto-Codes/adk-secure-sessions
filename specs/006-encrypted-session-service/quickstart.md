# Quickstart: Encrypted Session Service

**Feature Branch**: `006-encrypted-session-service`
**Date**: 2026-02-03

## Installation

```bash
pip install adk-secure-sessions
```

## Basic Usage

### Drop-in Replacement for DatabaseSessionService

```python
from adk_secure_sessions import FernetBackend, BACKEND_FERNET
from adk_secure_sessions.services import EncryptedSessionService

# Create encryption backend with your passphrase
backend = FernetBackend("your-secret-passphrase")

# Use as async context manager for automatic cleanup
async with EncryptedSessionService(
    db_path="sessions.db",
    backend=backend,
    backend_id=BACKEND_FERNET,
) as service:
    # Create a session with encrypted state
    session = await service.create_session(
        app_name="my-agent",
        user_id="user-123",
        state={"api_key": "sk-secret-key", "preferences": {"theme": "dark"}},
    )
    print(f"Created session: {session.id}")
```

### Retrieving Sessions

```python
# Get a specific session
session = await service.get_session(
    app_name="my-agent",
    user_id="user-123",
    session_id=session.id,
)

if session:
    print(f"State: {session.state}")  # Decrypted automatically
    print(f"Events: {len(session.events)}")

# Get only recent events
from google.adk.sessions.base_session_service import GetSessionConfig

session = await service.get_session(
    app_name="my-agent",
    user_id="user-123",
    session_id=session.id,
    config=GetSessionConfig(num_recent_events=10),
)
```

### Listing Sessions

```python
# List all sessions for an app
response = await service.list_sessions(app_name="my-agent")
for session in response.sessions:
    print(f"Session {session.id}: {session.user_id}")

# List sessions for a specific user
response = await service.list_sessions(
    app_name="my-agent",
    user_id="user-123",
)
```

### Deleting Sessions

```python
# Delete a session (cascades to events)
await service.delete_session(
    app_name="my-agent",
    user_id="user-123",
    session_id=session.id,
)
```

## With ADK Agents

### Replace DatabaseSessionService

Before (unencrypted):
```python
from google.adk.sessions import DatabaseSessionService

session_service = DatabaseSessionService(db_url="sqlite:///sessions.db")
```

After (encrypted):
```python
from adk_secure_sessions import FernetBackend, BACKEND_FERNET
from adk_secure_sessions.services import EncryptedSessionService

backend = FernetBackend("your-secret-passphrase")
session_service = EncryptedSessionService(
    db_path="sessions.db",
    backend=backend,
    backend_id=BACKEND_FERNET,
)
```

### Full Agent Example

```python
from google.adk import Agent
from google.adk.runners import Runner
from adk_secure_sessions import FernetBackend, BACKEND_FERNET
from adk_secure_sessions.services import EncryptedSessionService

# Create encrypted session service
backend = FernetBackend("your-secret-passphrase")

async with EncryptedSessionService(
    db_path="agent_sessions.db",
    backend=backend,
    backend_id=BACKEND_FERNET,
) as session_service:
    # Create your agent
    agent = Agent(
        name="my-agent",
        model="gemini-2.0-flash",
        system_instruction="You are a helpful assistant.",
    )

    # Create runner with encrypted session service
    runner = Runner(
        agent=agent,
        session_service=session_service,
        app_name="my-agent",
    )

    # Run the agent - all session data is encrypted automatically
    async for response in runner.run(
        user_id="user-123",
        user_message="Hello!",
    ):
        print(response)
```

## Error Handling

```python
from adk_secure_sessions import (
    SecureSessionError,
    EncryptionError,
    DecryptionError,
    SerializationError,
)
from google.adk.errors import AlreadyExistsError

try:
    session = await service.create_session(
        app_name="my-agent",
        user_id="user-123",
        state={"data": some_complex_object},
    )
except SerializationError:
    print("State contains non-JSON-serializable values")
except EncryptionError:
    print("Encryption failed")
except AlreadyExistsError:
    print("Session ID already exists")
except SecureSessionError:
    print("Other library error")
```

## Environment Variable Configuration

```python
import os
from adk_secure_sessions import FernetBackend, BACKEND_FERNET
from adk_secure_sessions.services import EncryptedSessionService

# Load passphrase from environment
passphrase = os.environ["SESSION_ENCRYPTION_KEY"]
backend = FernetBackend(passphrase)

session_service = EncryptedSessionService(
    db_path=os.environ.get("SESSION_DB_PATH", "sessions.db"),
    backend=backend,
    backend_id=BACKEND_FERNET,
)
```

## What Gets Encrypted

| Data | Encrypted? | Why |
|------|------------|-----|
| Session state | ✅ Yes | Contains sensitive user data |
| Event data | ✅ Yes | Contains conversation history |
| app_name | ❌ No | Needed for querying |
| user_id | ❌ No | Needed for querying |
| session_id | ❌ No | Needed for querying |
| Timestamps | ❌ No | Needed for ordering |

## Key Management Best Practices

1. **Never hardcode passphrases** - Use environment variables or secret managers
2. **Use strong passphrases** - At least 32 characters, high entropy
3. **Rotate keys periodically** - The envelope format supports backend migration
4. **Backup your keys** - Lost keys = lost data (no recovery possible)

```python
# Example with AWS Secrets Manager
import boto3
import json

def get_encryption_key():
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId="my-agent/session-key")
    return json.loads(response["SecretString"])["passphrase"]

backend = FernetBackend(get_encryption_key())
```
