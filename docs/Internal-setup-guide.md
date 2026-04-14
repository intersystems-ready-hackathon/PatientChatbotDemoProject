## Using Pre-built container on Artifactory

Step 1: 

Add a license key for IRISHealth + FHIR server to `iris/keys/IRISHealth.Key` (search for licence keys on confluence if needed).

Step 2: 

Add credentials for Artifactory to your docker config - instructions can be found online at docker.iscinternal.com


Step 3: 

Set-up gitlab access if not already

Step 4:

Clone repo with: 

```
git clone https://gitlab.iscinternal.com/tdyar/ready2026-hackathon

```

Step 4: 

Build container with: 

```
cd ReadyAI-demo 
docker-compose up --build -d 
```

## Build from Kit

Theres a separate build if you are building from kits. Kits can be downloaded from https://kits-web.iscinternal.com/kits/unreleased/IRISHealth/2026.2.0AI/

The dockerfile for this is in `ReadyAI-demo/iris4h-aihub-build`. 

The directories for the build kit, 