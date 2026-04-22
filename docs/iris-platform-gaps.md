# IRIS Platform & HealthShare Documentation Gaps

**Context:** Non-AI-Hub issues discovered while building the READY 2026 hackathon demo. These relate to general IRIS platform behavior, HealthShare/FHIR SQL Builder, and Docker infrastructure.

**Date:** 2026-04-01

---

## P1: Blocking

### 1. Docker Image: IRIS vs IRISHealth

**The problem:** The AI Hub EAP portal ships `iris-2026.2.0AI.141.0` (plain IRIS). For FHIR SQL Builder, you MUST use `IRISHealth` (e.g., `IRISHealth-2026.2.0AI.142.0`). The plain IRIS kit doesn't include `HS.FHIRServer.*`, `HS.HC.FHIRSQL.*`, or the FHIR SQL Builder UI. Nothing tells you this until you try to call `HS.FHIRServer.Installer` and get `<CLASS DOES NOT EXIST>`.

**Existing docs:**
- [IRIS containers](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=ADOCK) — good, but no IRIS vs IRISHealth comparison
- [IRIS for Health containers](https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=ADOCK) — separate doc set, implies the difference but doesn't state it
- [Container Registry](https://docs.intersystems.com/components/csp/docbook/DocBook.UI.Page.cls?KEY=PAGE_containerregistry) — lists both image types

**What's missing:** A clear statement: "IRISHealth includes HealthShare classes (HS.*, FHIR Server, FHIR SQL Builder). Plain IRIS does not. Both include the AI Hub."

---

## P2: Significant Time Savings

### 2. FHIR SQL Builder Programmatic Setup

**The problem:** The FHIR SQL Builder has a REST API at `/csp/fhirsql/api/ui/v1/...` but there is no documentation for driving it programmatically. We had to reverse-engineer the API by watching the Angular UI's network requests and building `FSBSetup.cls` from scratch.

**What we built** (`FSBSetup.cls`):
1. `HS.FHIRServer.Installer.InstallNamespace("READYAI")`
2. `HS.FHIRServer.Installer.InstallInstance(appKey, strategyClass, metadataPackages)`
3. `Ens.Director.StartProduction()`
4. `HS.FHIRServer.Tools.DataLoader.SubmitResourceFiles`
5. Enable `/csp/fhirsql/api/ui` and `/csp/fhirsql/api/repository` CSP apps
6. Grant `FSB_Admin`, `FSB_Analyst`, `FSB_Data_Steward` roles
7. REST API: POST credentials → POST fhirrepository → POST analysis (poll) → POST transformspec → POST projection

**Existing docs:**
- [FHIR SQL Builder](https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=FHIRSQL) — 6 sections covering UI workflow only
- [Install FHIR Server](https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=HXFHIR_server_install) — documents `HS.FHIRServer.Installer` but not the SQL Builder REST endpoints

**What's missing:** Full endpoint reference for `/csp/fhirsql/api/ui/v1/*` (credentials, fhirrepository, analysis, transformspec, projection).

### 3. `%Service_Bindings` Auth for Non-Privileged DB-API Users

**The problem:** Non-`%All` users cannot connect via `iris.connect()` (Python DB-API) unless `%Service_Bindings` has password auth enabled. The `aicore-iris:140` base image had `AutheEnabled=96` (Kerberos-only), blocking all non-%All users. We worked around by giving Doctor/Nurse the `%All` role.

**Existing docs:**
- [Managing Services](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GSA_manage_services) — covers service configuration
- [Authentication Overview](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=AAUTHN) — covers auth mechanisms
- [Python DB-API intro](https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=BPYDBAPI_about) — covers `iris.connect()`

**What's missing:** None of these connect the dots: "to connect via Python DB-API, `%Service_Bindings` must have password auth enabled for non-%All users." The `AutheEnabled` bitmask values (1=unauthenticated, 4=password, 64=delegated, 96=Kerberos) are not documented for `%Service_Bindings` specifically.

### 4. Ensemble Production Must Be Running for FHIR Data Loading

**The problem:** `HS.FHIRServer.Tools.DataLoader.SubmitResourceFiles()` silently does nothing if the Interoperability production isn't running. We had to discover `Ens.Director.StartProduction()` was a prerequisite.

**Existing docs:**
- [Install FHIR Server](https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=HXFHIR_server_install) — production is started as part of `InstallNamespace`, but the `DataLoader` prerequisite is not called out

**What's missing:** A note in the DataLoader docs: "The Interoperability production must be running before calling SubmitResourceFiles."

---

## P3: Nice to Have

### 5. IPM `WebApplication` Element

We auto-registered the MCP CSP web app via `module.xml`:
```xml
<WebApplication Url="/mcp/readyAI" AutheEnabled="64"
    DispatchClass="ReadyAI.MCPService" MatchRoles=":%All"/>
```

**Existing docs:** No official docs.intersystems.com page. Community resources only:
- [Anatomy of a ZPM Module](https://community.intersystems.com/post/anatomy-zpm-module-packaging-your-intersystems-solution)
- [Describing module.xml](https://community.intersystems.com/post/describing-module-xml-objectscript-package-manager)
- [ZPM + CSP pages](https://community.intersystems.com/post/zpm-adding-csp-pages-existing-namespace)

**What's missing:** Formal reference for the `WebApplication` XML element in the [IPM GitHub repo](https://github.com/intersystems/ipm) or docs.intersystems.com.

---

## Reference Links

| Topic | URL | Coverage |
|---|---|---|
| IRIS containers | https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=ADOCK | Good — no IRIS vs IRISHealth comparison |
| IRIS for Health containers | https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=ADOCK | Separate doc set |
| Container Registry | https://docs.intersystems.com/components/csp/docbook/DocBook.UI.Page.cls?KEY=PAGE_containerregistry | Lists both image types |
| Managing Services | https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GSA_manage_services | `%Service_Bindings` config |
| Authentication mechanisms | https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=AAUTHN | AutheEnabled values |
| Python DB-API | https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=BPYDBAPI_about | Connection setup |
| CSP web app config | https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=GCSP_appdef | AutheEnabled for CSP apps |
| FHIR SQL Builder | https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=FHIRSQL | UI workflow only |
| Install FHIR Server | https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=HXFHIR_server_install | HS.FHIRServer.Installer |
| Secrets Management | https://docs.intersystems.com/irislatest/csp/docbook/DocBook.UI.Page.cls?KEY=ROARS_secrets_mgmt | %Wallet API |

---

## Action Items

| # | Action | Area | Priority |
|---|---|---|---|
| 1 | List IRISHealth AI variant on EAP portal | IRIS Packaging | P1 |
| 2 | Document FHIR SQL Builder REST API for programmatic setup | HealthShare / FHIR SQL Builder team | P2 |
| 3 | Document `%Service_Bindings` auth for non-%All DB-API users | IRIS Security docs | P2 |
| 4 | Document `Ens.Director.StartProduction` prerequisite for FHIR data loading | HealthShare FHIR Server docs | P2 |
| 5 | Document IPM `WebApplication` element for CSP app auto-registration | IPM / ZPM docs | P3 |
