"""
Seed the IRIS ConfigStore with a demo OpenAI provider registration.

Creates the AIGateway_Storage.LLMProvider table (if needed) and inserts
an 'openai-demo' provider entry — mimicking what Jane does in the Management
Portal in the user story.

Usage:
    python seed_configstore.py

Environment variables:
    IRIS_PORT        (default: 1972)
    IRIS_HOSTNAME    (default: localhost)
    IRIS_NAMESPACE   (default: USER)
    IRIS_USERNAME    (default: _SYSTEM)
    IRIS_PASSWORD    (default: SYS)
"""

import os
import iris.dbapi

PROVIDER_NAME = "openai-demo"
MODEL = "gpt-4o-mini"

connect_kwargs = {
    "hostname": os.environ.get("IRIS_HOSTNAME", "localhost"),
    "port": int(os.environ.get("IRIS_PORT", "1972")),
    "namespace": os.environ.get("IRIS_NAMESPACE", "USER"),
    "username": os.environ.get("IRIS_USERNAME", "_SYSTEM"),
    "password": os.environ.get("IRIS_PASSWORD", "SYS"),
}

conn = iris.dbapi.connect(**connect_kwargs)
cur = conn.cursor()

# Create schema/table if it doesn't exist
cur.execute("""
    CREATE TABLE IF NOT EXISTS AIGateway_Storage.LLMProvider (
        Name            VARCHAR(64)  NOT NULL,
        ProviderType    VARCHAR(32)  NOT NULL,
        DefaultModel    VARCHAR(128),
        ApiBaseUrl      VARCHAR(512),
        CredentialRef   VARCHAR(256),
        Enabled         INTEGER      DEFAULT 1,
        Description     VARCHAR(512),
        CONSTRAINT LLMProviderPK PRIMARY KEY (Name)
    )
""")
conn.commit()
print("✓ AIGateway_Storage.LLMProvider table ensured")

# Upsert the demo provider
cur.execute("DELETE FROM AIGateway_Storage.LLMProvider WHERE Name = ?", [PROVIDER_NAME])
cur.execute(
    """
    INSERT INTO AIGateway_Storage.LLMProvider
        (Name, ProviderType, DefaultModel, CredentialRef, Enabled, Description)
    VALUES (?, ?, ?, ?, 1, ?)
""",
    [
        PROVIDER_NAME,
        "openai",
        MODEL,
        "env:OPENAI_API_KEY",  # demo: real ConfigStore uses iris-wallet://
        "Demo OpenAI provider for READY 2026 hackathon",
    ],
)
conn.commit()
print(f"✓ Registered provider '{PROVIDER_NAME}' (model={MODEL})")

cur.execute(
    "SELECT Name, ProviderType, DefaultModel, Description FROM AIGateway_Storage.LLMProvider"
)
rows = cur.fetchall()
print("\nCurrent ConfigStore entries:")
for row in rows:
    print(f"  {row[0]:20s}  type={row[1]:10s}  model={row[2]}")

conn.close()
