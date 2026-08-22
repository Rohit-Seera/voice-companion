"""Global pytest configuration."""

import os


# ---------------------------------------------------------------------------
# Test-only security configuration
# ---------------------------------------------------------------------------
#
# These values are used only by the pytest process.
# They must never be used as production credentials.
# ---------------------------------------------------------------------------

os.environ["SECURITY_JWT_SECRET_KEY"] = (
    "test-only-weings-ai-jwt-secret-"
    "9f4c7b2a6e1d8c3f5a7b0e4d6c8f2a1"
    "7b5e9d3c1a6f8e2b"
    "4d8a1f6c9e3b7a2d"
)

os.environ["SECURITY_JWT_ALGORITHM"] = "HS256"

os.environ["SECURITY_JWT_ISSUER"] = "weings-ai"

os.environ["SECURITY_JWT_AUDIENCE"] = "weings-ai-client"