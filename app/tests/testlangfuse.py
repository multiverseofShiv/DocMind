import os

from app.core.config import get_settings



os.environ["LANGFUSE_HOST"] = "http://langfuse:3000"

settings = get_settings()
print("LANGFUSE HOST:", settings.langfuse_host)
print("LANGFUSE KEY:", settings.langfuse_public_key[:10] if settings.langfuse_public_key else None)

import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("langfuse").setLevel(logging.DEBUG)

from langfuse import Langfuse

client = Langfuse(
public_key='pk-lf-cae3c4d5-998e-4eec-9d32-e8e52929a1a7',
secret_key='sk-lf-ba872e29-a777-44c1-9e25-184e86d1a021',
    host="http://localhost:3000"
)

print("Auth:", client.auth_check())

trace = client.trace(
    name="chat",
    user_id="test-tenant",
    input="what is this document about?",
    output="this document is about xyz",
    metadata={"latency_ms": 500},
    tags=["chat", "production"],
)

print("Trace ID:", trace.id)
result = client.flush()
print("Flush result:", result)
print("Done.")
