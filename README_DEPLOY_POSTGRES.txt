# VisionX ERP API PostgreSQL Deployment Notes

Current version-check API works with environment variables only.

PostgreSQL is optional for the next stage when we add:

- License customer table
- Activated machines table
- Update channels table
- Customer-specific edition/limits
- Activation history / audit log

## Suggested future Render variables

```txt
DATABASE_URL=<Render PostgreSQL internal/external URL>
VISIONX_LICENSE_PRIVATE_KEY_B64=<private key stored only in Render>
```

## Suggested future tables

```sql
customers
licenses
activations
update_channels
audit_log
```

## Current API without PostgreSQL

For update checking only, these are enough:

```txt
VISIONX_LATEST_VERSION
VISIONX_VERSION_LABEL
VISIONX_DOWNLOAD_URL
VISIONX_DOWNLOAD_SHA256
VISIONX_RELEASE_NOTES
VISIONX_FORCE_UPDATE
VISIONX_PRODUCT
VISIONX_CHANNEL
```
