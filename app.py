import os
from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name, default) or "").strip()


def _bool_env(name: str, default: bool = False) -> bool:
    value = _env(name, "true" if default else "false").lower()
    return value in {"1", "true", "yes", "y", "on"}


def _channel_prefix(channel: str) -> str:
    ch = (channel or "standard").strip().lower()
    if ch in {"pro", "plus"}:
        return f"VISIONX_{ch.upper()}_"
    return "VISIONX_"


def _edition_name(channel: str) -> str:
    ch = (channel or "standard").strip().lower()
    if ch == "pro":
        return "PRO"
    if ch == "plus":
        return "PLUS"
    return "STANDARD"


def _env_by_channel(channel: str, suffix: str, default: str = "") -> str:
    """Read edition-specific env first, then fallback to old/generic Standard keys.

    Examples:
    pro + VERSION       -> VISIONX_PRO_VERSION, fallback VISIONX_LATEST_VERSION
    pro + URL           -> VISIONX_PRO_URL, fallback VISIONX_DOWNLOAD_URL
    pro + SHA256        -> VISIONX_PRO_SHA256, fallback VISIONX_DOWNLOAD_SHA256
    standard + VERSION  -> VISIONX_LATEST_VERSION
    """
    ch = (channel or "standard").strip().lower()
    if ch in {"pro", "plus"}:
        prefix = f"VISIONX_{ch.upper()}_"
        val = _env(prefix + suffix)
        if val:
            return val

    # Generic / Standard compatibility keys
    fallback_map = {
        "VERSION": "VISIONX_LATEST_VERSION",
        "URL": "VISIONX_DOWNLOAD_URL",
        "SHA256": "VISIONX_DOWNLOAD_SHA256",
        "CHANNEL": "VISIONX_CHANNEL",
        "VERSION_LABEL": "VISIONX_VERSION_LABEL",
        "GITHUB_RELEASE_TAG": "VISIONX_GITHUB_RELEASE_TAG",
        "FORCE_UPDATE": "VISIONX_FORCE_UPDATE",
        "RELEASE_NOTES": "VISIONX_RELEASE_NOTES",
        "PRODUCT": "VISIONX_PRODUCT",
        "EDITION": "VISIONX_EDITION",
    }
    return _env(fallback_map.get(suffix, "VISIONX_" + suffix), default)


def _version_payload() -> dict:
    client_channel = (
        request.args.get("channel")
        or request.args.get("edition")
        or _env("VISIONX_CHANNEL", "standard")
    ).strip().lower()

    if client_channel not in {"standard", "plus", "pro"}:
        client_channel = "standard"

    latest_version = _env_by_channel(client_channel, "VERSION", "v1.0.13")
    product = _env_by_channel(client_channel, "PRODUCT", _env("VISIONX_PRODUCT", "VISIONX_ERP_DESKTOP")) or "VISIONX_ERP_DESKTOP"
    channel = _env_by_channel(client_channel, "CHANNEL", client_channel) or client_channel

    # Support both old and new SHA names.
    sha256_value = (
        _env_by_channel(client_channel, "SHA256")
        or _env_by_channel(client_channel, "DOWNLOAD_SHA256")
        or _env("VISIONX_SHA256")
    )

    version_label = (
        _env_by_channel(client_channel, "VERSION_LABEL")
        or f"VisionX ERP {latest_version}"
    )

    return {
        "ok": True,
        "product": product,
        "channel": channel,
        "edition": _env_by_channel(client_channel, "EDITION", _edition_name(client_channel)),
        "latest_version": latest_version,
        "version": latest_version,
        "version_label": version_label,
        "latest_version_label": version_label,
        "github_release_tag": _env_by_channel(client_channel, "GITHUB_RELEASE_TAG", latest_version),
        "download_url": _env_by_channel(client_channel, "URL"),
        "sha256": sha256_value,
        "download_sha256": sha256_value,
        "force_update": _bool_env(f"VISIONX_{client_channel.upper()}_FORCE_UPDATE", _bool_env("VISIONX_FORCE_UPDATE", False)) if client_channel in {"plus", "pro"} else _bool_env("VISIONX_FORCE_UPDATE", False),
        "release_notes": _env_by_channel(client_channel, "RELEASE_NOTES", "VisionX ERP update"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/")
def index():
    return jsonify({
        "ok": True,
        "service": "VisionX ERP API",
        "message": "Use /health or /visionx/latest-version",
    })


@app.route("/health")
@app.route("/health/")
def health():
    return jsonify({
        "ok": True,
        "service": "visionx-erp-api",
        "status": "healthy",
        "time_utc": datetime.now(timezone.utc).isoformat(),
    })


@app.route("/visionx/latest-version")
@app.route("/visionx/latest-version/")
def latest_version():
    payload = _version_payload()
    payload["client"] = {
        "product": request.args.get("product", ""),
        "channel": request.args.get("channel", ""),
        "version": request.args.get("version", ""),
        "current_version": request.args.get("current_version", ""),
    }

    if not payload.get("download_url"):
        payload["ok"] = False
        payload["message"] = f"Download URL not configured for channel {payload.get('channel')}"
    elif not payload.get("sha256"):
        payload["ok"] = False
        payload["message"] = f"SHA256 not configured for channel {payload.get('channel')}"
    else:
        payload["message"] = "Update information loaded."

    return jsonify(payload)


@app.post("/visionx/activate")
def activate():
    return jsonify({
        "ok": False,
        "message": "Activation API placeholder. VX2 private-key signing will be added later.",
    }), 501


@app.post("/visionx/verify-license")
def verify_license():
    return jsonify({
        "ok": False,
        "message": "License verification API placeholder. VX2 verify endpoint will be added later.",
    }), 501


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
