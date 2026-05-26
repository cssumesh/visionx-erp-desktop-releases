import os
from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name, default) or "").strip()


def _bool_env(name: str, default: bool = False) -> bool:
    value = _env(name, "true" if default else "false").lower()
    return value in {"1", "true", "yes", "y", "on"}


def _version_payload() -> dict:
    latest_version = _env("VISIONX_LATEST_VERSION", "v1.0.13")
    product = _env("VISIONX_PRODUCT", "VISIONX_ERP_DESKTOP")
    channel = _env("VISIONX_CHANNEL", "standard")

    # Support both names. VISIONX_DOWNLOAD_SHA256 is preferred.
    sha256_value = _env("VISIONX_DOWNLOAD_SHA256") or _env("VISIONX_SHA256")

    return {
        "ok": True,
        "product": product,
        "channel": channel,
        "edition": _env("VISIONX_EDITION", "DESKTOP_LOCAL"),
        "latest_version": latest_version,
        "version_label": _env("VISIONX_VERSION_LABEL", f"VisionX ERP {latest_version}"),
        "github_release_tag": _env("VISIONX_GITHUB_RELEASE_TAG", latest_version),
        "download_url": _env("VISIONX_DOWNLOAD_URL"),
        "sha256": sha256_value,
        "force_update": _bool_env("VISIONX_FORCE_UPDATE", False),
        "release_notes": _env("VISIONX_RELEASE_NOTES", "VisionX ERP update"),
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
    }
    return jsonify(payload)


@app.post("/visionx/activate")
def activate():
    # Placeholder for the next license-server step.
    # Keep private signing key only in Render environment variables, never in customer EXE.
    return jsonify({
        "ok": False,
        "message": "Activation API placeholder. VX2 private-key signing will be added later.",
    }), 501


@app.post("/visionx/verify-license")
def verify_license():
    # Placeholder for online verification, optional for Desktop/Local.
    return jsonify({
        "ok": False,
        "message": "License verification API placeholder. VX2 verify endpoint will be added later.",
    }), 501


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
