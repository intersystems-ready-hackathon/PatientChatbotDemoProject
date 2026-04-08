# AGENTS.md — ReadyAI-demo/iris/

IRIS Docker container: FHIR data, MCP server, ObjectScript tools.
Mounted at `/home/irisowner/dev` inside container via `projects/`.

## Structure

```
iris/
├── Dockerfile              # Custom IRIS build (IPM install, FHIR load, roleSetup)
├── iris.cpf                # IRIS configuration (namespaces, startup)
├── iris.script             # Runs at build time: namespace setup, package install
├── roleSetup.script        # Creates Doctor/Nurse IRIS roles
├── requirements.txt        # Python packages installed into IRIS container
├── fhirsampledata/         # 121 synthetic FHIR patient JSON bundles
├── resources/webgateway/   # Webgateway config for MCP web app
└── projects/               # Mounted as /home/irisowner/dev
    ├── config.toml         # iris-mcp-server config (port 8888, HTTP transport)
    ├── config-stdio.toml   # Alternative stdio transport config
    ├── module.xml          # IPM package manifest
    ├── ObjectScript/       # .cls tool classes
    └── FHIR/               # FHIR SQL Builder setup request bodies
```

## Key Facts

- Namespace: `READYAI`
- MCP server port: `8888` (HTTP transport, `0.0.0.0`)
- IRIS superserver: `1972` (DB-API), `1973` (legacy port used in app code)
- IRIS web gateway: `32783` (Docker-exposed) → MCP health at `/mcp/readyAI/v1/health`

## FHIR SQL Builder Setup

Automated via `Setup.FSB` ObjectScript class. Run once after first `docker-compose up`:

```bash
python3 scripts/fhir_setup.py
```

Takes 5-10 minutes. Creates 119 patients × AFHIRData tables (Patient, Observation, Condition, DocumentReference).

**What it does** (via `Setup.FSB.RunAll`):
1. `InstallFHIRServer` — installs FHIR R4 server at `/readyai/r4`, loads 121 patient JSON bundles from `/tmp/fhirdata`
2. `EnableApps` — enables `/csp/fhirsql/api/ui` and `/csp/fhirsql/api/repository` CSP apps with Password auth
3. `GrantFSBRoles` — grants `FSB_Admin`, `FSB_Analyst`, `FSB_Data_Steward` to all test users
4. REST API calls to FHIR SQL Builder: credentials → fhirrepository → analysis → transformspec → projection

**Why not in Dockerfile**: analysis takes 5-10 minutes — too slow for `docker build`.

**Note**: `FSB.cls` must be copied to `/tmp` before loading because the volume mount (`/home/irisowner/dev`) is owned by root but IRIS runs as `irisowner`.

## Vector Store Setup

```objectscript
zn "READYAI"
do ##class(RAG.DocRefVectorSetup).EmbedText()
```

Creates global `AFHIRData.DocRefVectorStore` from `DocumentReference` FHIR resources.

## Anti-Patterns

- Do NOT run FHIR SQL Builder POSTs during Docker build — web-gateway not ready
- Do NOT hardcode connection strings in Python — use `iris-mcp-server` managed connections
- Do NOT add `iris.key` or any `.key`/`.lic` files here — never commit license files
