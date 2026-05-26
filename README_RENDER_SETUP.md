# VisionX ERP Render API Setup

This repo is for the private Render API used by VisionX ERP Desktop / Local.

## Endpoints

- `/`
- `/health`
- `/visionx/latest-version`
- `/visionx/activate` placeholder
- `/visionx/verify-license` placeholder

## Render Web Service Settings

Use:

```txt
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

## Required Environment Variables

```txt
VISIONX_LATEST_VERSION=v1.0.17
VISIONX_VERSION_LABEL=VisionX ERP v1.0.17
VISIONX_PRODUCT=VISIONX_ERP_DESKTOP
VISIONX_CHANNEL=standard
VISIONX_EDITION=DESKTOP_LOCAL
VISIONX_GITHUB_RELEASE_TAG=v1.0.17
VISIONX_DOWNLOAD_URL=https://github.com/cssumesh/visionx-erp-desktop-releases/releases/download/v1.0.17/<asset-name>
VISIONX_DOWNLOAD_SHA256=<GitHub SHA256 of exact uploaded asset>
VISIONX_FORCE_UPDATE=false
VISIONX_RELEASE_NOTES=VisionX ERP v1.0.17 update
```

`VISIONX_DOWNLOAD_SHA256` is preferred. `VISIONX_SHA256` is also accepted as fallback.

## Test URLs

```txt
https://visionx-erp-api.onrender.com/health
https://visionx-erp-api.onrender.com/visionx/latest-version
https://visionx-erp-api.onrender.com/visionx/latest-version?product=VISIONX_ERP_DESKTOP&channel=standard&version=v1.0.13
```

## Important Security Note

Do not store private license signing keys in GitHub or inside the customer EXE. Keep private keys only in Render environment variables or on the owner's offline key generator machine.
