import os
import re
from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)

# =============================================================================
# VisionX ERP Desktop Releases / Render Update API
# GitHub file name must be: app.py
# Render start command: gunicorn app:app
# =============================================================================

SERVICE_NAME = "VisionX ERP Desktop Releases API"
API_VERSION = "desktop-releases-channel-v1"


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name, default) or "").strip()


def _bool(value: str, default: bool = False) -> bool:
    text = (value or "").strip().lower()
    if not text:
        return default
    return text in {"1", "true", "yes", "y", "on"}


def _canonical_channel(value: str) -> str:
    text = (value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if text in {"pro", "professional", "ai", "pro_ai", "visionx_pro"}:
        return "pro"
    if text in {"plus", "clinic", "clinic_optical", "clinic_optical_pharmacy", "visionx_plus"}:
        return "plus"
    return "standard"


def _edition(channel: str) -> str:
    return {"standard": "STANDARD", "plus": "PLUS", "pro": "PRO"}.get(_canonical_channel(channel), "STANDARD")


def _requested_channel() -> str:
    return _canonical_channel(
        request.args.get("channel")
        or request.args.get("edition")
        or request.headers.get("X-VisionX-Channel")
        or _env("VISIONX_DEFAULT_CHANNEL")
        or "standard"
    )


def _requested_product() -> str:
    return (
        request.args.get("product")
        or request.headers.get("X-VisionX-Product")
        or _env("VISIONX_PRODUCT", "VISIONX_ERP_DESKTOP")
        or "VISIONX_ERP_DESKTOP"
    ).strip()


def _current_version() -> str:
    return (
        request.args.get("current_version")
        or request.args.get("version")
        or request.headers.get("X-VisionX-Version")
        or ""
    ).strip()


def _get_channel_env(channel: str, suffix: str, default: str = "") -> str:
    channel = _canonical_channel(channel)
    suffix = (suffix or "").strip().upper()
    prefix = f"VISIONX_{channel.upper()}_"

    keys = [prefix + suffix]
    if suffix == "VERSION":
        keys.append(prefix + "LATEST_VERSION")
    elif suffix == "URL":
        keys.append(prefix + "DOWNLOAD_URL")
    elif suffix == "SHA256":
        keys.append(prefix + "DOWNLOAD_SHA256")

    # Old generic variables are fallback only for Standard.
    # This prevents Pro/Plus accidentally receiving Standard values.
    if channel == "standard":
        fallback = {
            "VERSION": ["VISIONX_LATEST_VERSION", "VISIONX_VERSION"],
            "URL": ["VISIONX_DOWNLOAD_URL", "VISIONX_URL"],
            "SHA256": ["VISIONX_DOWNLOAD_SHA256", "VISIONX_SHA256"],
            "VERSION_LABEL": ["VISIONX_VERSION_LABEL"],
            "RELEASE_NOTES": ["VISIONX_RELEASE_NOTES"],
            "FORCE_UPDATE": ["VISIONX_FORCE_UPDATE"],
            "GITHUB_RELEASE_TAG": ["VISIONX_GITHUB_RELEASE_TAG"],
        }
        keys.extend(fallback.get(suffix, []))

    for key in keys:
        value = _env(key)
        if value:
            return value
    return default


def _normalize_version(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    return value if value.lower().startswith("v") else "v" + value


def _version_tuple(value: str):
    nums = re.findall(r"\d+", (value or "").lstrip("vV"))
    parts = [int(x) for x in nums[:4]]
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts)


def _update_available(current: str, latest: str) -> bool:
    try:
        if not current or not latest:
            return False
        return _version_tuple(latest) > _version_tuple(current)
    except Exception:
        return False


def _valid_url(url: str) -> bool:
    url = (url or "").strip()
    return url.startswith("https://") or url.startswith("http://")


def _valid_sha256(value: str) -> bool:
    return bool(re.fullmatch(r"[a-fA-F0-9]{64}", (value or "").strip()))


def _is_placeholder(value: str) -> bool:
    text = (value or "").strip().upper()
    return (not text) or text.startswith("PASTE_") or text.startswith("<") or text.endswith("_HERE")


def _payload() -> dict:
    channel = _requested_channel()
    current = _normalize_version(_current_version())
    latest = _normalize_version(_get_channel_env(channel, "VERSION", "v1.0.12"))
    url = _get_channel_env(channel, "URL", "")
    sha = _get_channel_env(channel, "SHA256", "").lower()

    version_label = _get_channel_env(channel, "VERSION_LABEL", "") or f"VisionX ERP {_edition(channel).title()} {latest}"
    release_notes = _get_channel_env(channel, "RELEASE_NOTES", "") or "VisionX ERP update available."
    force_update = _bool(_get_channel_env(channel, "FORCE_UPDATE", "false"), False)
    release_tag = _get_channel_env(channel, "GITHUB_RELEASE_TAG", latest) or latest

    download_ready = _valid_url(url) and not _is_placeholder(url)
    sha_ready = _valid_sha256(sha) and not _is_placeholder(sha)
    is_update = _update_available(current, latest)

    ok = True
    message = "Update information loaded."
    if not download_ready:
        ok = False
        message = f"Download URL is not configured in Render for {channel}. Set VISIONX_{channel.upper()}_URL."
    elif not sha_ready:
        ok = False
        message = f"Valid SHA256 is not configured in Render for {channel}. Set VISIONX_{channel.upper()}_SHA256."
    elif not is_update:
        message = "App is up to date."

    now = datetime.now(timezone.utc).isoformat()
    product = _env("VISIONX_PRODUCT", "VISIONX_ERP_DESKTOP") or "VISIONX_ERP_DESKTOP"

    # Old + new field names are both returned for compatibility with older VisionX builds.
    return {
        "ok": ok,
        "service": SERVICE_NAME,
        "api_version": API_VERSION,
        "product": product,
        "requested_product": _requested_product(),
        "channel": channel,
        "requested_channel": channel,
        "edition": _edition(channel),
        "current_version": current,
        "latest_version": latest,
        "version": latest,
        "version_label": version_label,
        "latest_version_label": version_label,
        "github_release_tag": release_tag,
        "release_notes": release_notes,
        "force_update": force_update,
        "download_url": url if download_ready else "",
        "url": url if download_ready else "",
        "sha256": sha if sha_ready else "",
        "download_sha256": sha if sha_ready else "",
        "download_ready": download_ready,
        "sha256_ready": sha_ready,
        "update_available": bool(is_update and download_ready and sha_ready),
        "message": message,
        "generated_at": now,
        "updated_at": now,
    }


@app.get("/")
def index():
    return jsonify({
        "ok": True,
        "service": SERVICE_NAME,
        "api_version": API_VERSION,
        "message": "VisionX ERP DESKTOP-RELEASES APP.PY RUNNING",
        "endpoints": ["/health", "/visionx/latest-version", "/latest-version", "/visionx/env-check"],
    })


@app.get("/health")
@app.get("/health/")
def health():
    return jsonify({
        "ok": True,
        "service": SERVICE_NAME,
        "api_version": API_VERSION,
        "status": "healthy",
        "time_utc": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/visionx/latest-version")
@app.get("/visionx/latest-version/")
@app.get("/latest-version")
@app.get("/latest-version/")
def latest_version():
    return jsonify(_payload()), 200


@app.get("/visionx/env-check")
def env_check():
    channels = {}
    for channel in ("standard", "plus", "pro"):
        url = _get_channel_env(channel, "URL", "")
        sha = _get_channel_env(channel, "SHA256", "")
        channels[channel] = {
            "version": _get_channel_env(channel, "VERSION", ""),
            "version_label": _get_channel_env(channel, "VERSION_LABEL", ""),
            "url_present": bool(url),
            "url_valid": _valid_url(url),
            "url_preview": (url[:70] + "...") if len(url) > 75 else url,
            "sha256_present": bool(sha),
            "sha256_valid": _valid_sha256(sha),
            "sha256_length": len(sha or ""),
        }
    return jsonify({
        "ok": True,
        "service": SERVICE_NAME,
        "api_version": API_VERSION,
        "product": _env("VISIONX_PRODUCT", "VISIONX_ERP_DESKTOP"),
        "default_channel": _env("VISIONX_DEFAULT_CHANNEL", "standard"),
        "channels": channels,
    })


@app.post("/visionx/activate")
def activate():
    return jsonify({"ok": False, "message": "Activation API placeholder."}), 501


@app.post("/visionx/verify-license")
def verify_license():
    return jsonify({"ok": False, "message": "License verification API placeholder."}), 501


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
