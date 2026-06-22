import os
from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name, default) or "").strip()


def _bool_text(value: str, default: bool = False) -> bool:
    text = (value if value != "" else ("true" if default else "false")).strip().lower()
    return text in {"1", "true", "yes", "y", "on"}


def _bool_env(name: str, default: bool = False) -> bool:
    return _bool_text(_env(name), default)


def _canonical_channel(value: str) -> str:
    text = (value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if text in {"pro", "professional", "ai", "pro_ai"}:
        return "pro"
    if text in {"plus", "clinic", "clinic_optical", "clinic_optical_pharmacy"}:
        return "plus"
    return "standard"


def _edition_name(channel: str) -> str:
    ch = _canonical_channel(channel)
    if ch == "pro":
        return "PRO"
    if ch == "plus":
        return "PLUS"
    return "STANDARD"


def _edition_env(channel: str, *suffixes: str, default: str = "") -> str:
    """Read edition-specific keys first, then old/generic keys.

    For Standard:
      VISIONX_STANDARD_VERSION / URL / SHA256 are preferred.
      Old generic keys VISIONX_LATEST_VERSION / DOWNLOAD_URL / DOWNLOAD_SHA256 are fallback.

    For Plus:
      VISIONX_PLUS_VERSION / URL / SHA256 are preferred.

    For Pro:
      VISIONX_PRO_VERSION / URL / SHA256 are preferred.
    """
    ch = _canonical_channel(channel)
    prefix = f"VISIONX_{ch.upper()}_"

    for suffix in suffixes:
        s = str(suffix or "").strip().upper()
        if not s:
            continue
        for key in (
            prefix + s,
            prefix + ("DOWNLOAD_" + s if s in {"URL", "SHA256"} else s),
        ):
            val = _env(key)
            if val:
                return val

    # Backward-compatible fallback for older Standard-only API setup.
    generic_map = {
        "VERSION": ["VISIONX_LATEST_VERSION", "VISIONX_VERSION"],
        "LATEST_VERSION": ["VISIONX_LATEST_VERSION", "VISIONX_VERSION"],
        "URL": ["VISIONX_DOWNLOAD_URL", "VISIONX_URL"],
        "DOWNLOAD_URL": ["VISIONX_DOWNLOAD_URL", "VISIONX_URL"],
        "SHA256": ["VISIONX_DOWNLOAD_SHA256", "VISIONX_SHA256"],
        "DOWNLOAD_SHA256": ["VISIONX_DOWNLOAD_SHA256", "VISIONX_SHA256"],
        "CHANNEL": ["VISIONX_CHANNEL"],
        "VERSION_LABEL": ["VISIONX_VERSION_LABEL"],
        "GITHUB_RELEASE_TAG": ["VISIONX_GITHUB_RELEASE_TAG"],
        "FORCE_UPDATE": ["VISIONX_FORCE_UPDATE"],
        "RELEASE_NOTES": ["VISIONX_RELEASE_NOTES"],
        "PRODUCT": ["VISIONX_PRODUCT"],
        "EDITION": ["VISIONX_EDITION"],
    }
    for suffix in suffixes:
        for key in generic_map.get(str(suffix or "").strip().upper(), []):
            val = _env(key)
            if val:
                return val

    return default


def _request_channel() -> str:
    return _canonical_channel(
        request.args.get("channel")
        or request.args.get("edition")
        or _env("VISIONX_DEFAULT_CHANNEL")
        or _env("VISIONX_CHANNEL")
        or "standard"
    )


def _version_payload() -> dict:
    channel = _request_channel()
    edition = _edition_name(channel)

    latest_version = (
        _edition_env(channel, "VERSION", "LATEST_VERSION")
        or ("v1.0.13")
    )

    product = (
        _edition_env(channel, "PRODUCT")
        or _env("VISIONX_PRODUCT", "VISIONX_ERP_DESKTOP")
        or "VISIONX_ERP_DESKTOP"
    )

    download_url = _edition_env(channel, "URL", "DOWNLOAD_URL")
    sha256_value = _edition_env(channel, "SHA256", "DOWNLOAD_SHA256")

    version_label = (
        _edition_env(channel, "VERSION_LABEL")
        or f"VisionX ERP {edition.title()} {latest_version}"
    )

    github_release_tag = (
        _edition_env(channel, "GITHUB_RELEASE_TAG")
        or _env("VISIONX_GITHUB_RELEASE_TAG")
        or latest_version
    )

    force_update = _bool_text(
        _edition_env(channel, "FORCE_UPDATE", default=_env("VISIONX_FORCE_UPDATE", "false")),
        False,
    )

    payload = {
        "ok": True,
        "product": product,
        "channel": channel,
        "edition": _edition_env(channel, "EDITION") or edition,
        "latest_version": latest_version,
        "version": latest_version,
        "version_label": version_label,
        "latest_version_label": version_label,
        "github_release_tag": github_release_tag,
        "download_url": download_url,
        "sha256": sha256_value,
        "download_sha256": sha256_value,
        "force_update": force_update,
        "release_notes": _edition_env(channel, "RELEASE_NOTES", default="VisionX ERP update"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if not download_url:
        payload["ok"] = False
        payload["message"] = f"Download URL not configured for channel {channel}. Set VISIONX_{channel.upper()}_URL in Render."
    elif not sha256_value or len(sha256_value.strip()) != 64:
        payload["ok"] = False
        payload["message"] = f"Valid SHA256 not configured for channel {channel}. Set VISIONX_{channel.upper()}_SHA256 in Render."
    else:
        payload["message"] = "Update information loaded."

    return payload


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
        "edition": request.args.get("edition", ""),
        "version": request.args.get("version", ""),
        "current_version": request.args.get("current_version", ""),
    }
    return jsonify(payload), 200


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
