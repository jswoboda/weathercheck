#!/usr/bin/env python3
"""
Check TLS certificates against an MQTT broker.

Usage:
    python check_mqtt_tls.py --cfg.broker mqtt.example.com \
                              --cfg.ca_cert ca.pem \
                              --cfg.certfile client.crt \
                              --cfg.keyfile  client.key

    # Or via config file:
    python check_mqtt_tls.py --config tls_check.yaml
"""

import ssl
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiomqtt
import anyio
from jsonargparse import ArgumentParser

try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend

    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

# ── Symbols ───────────────────────────────────────────────────────────────────
PASS = "✓"
FAIL = "✗"
WARN = "⚠"
SEP = "─" * 54


# ── Config dataclass ──────────────────────────────────────────────────────────
@dataclass
class Config:
    broker: str
    port: int = 8883
    ca_cert: Optional[Path] = None  # CA / root certificate
    certfile: Optional[Path] = None  # client certificate
    keyfile: Optional[Path] = None  # client private key
    timeout: float = 10.0  # connection timeout (seconds)
    verify_hostname: bool = True
    client_id: str = "tls_checker"


# ── File checks ───────────────────────────────────────────────────────────────
def check_file_exists(path: Optional[Path], label: str) -> bool:
    if path is None:
        print(f"  {WARN}  {label:<16} not provided (optional)")
        return True
    if not path.exists():
        print(f"  {FAIL}  {label:<16} not found  →  {path}")
        return False
    print(f"  {PASS}  {label:<16} found     →  {path}")
    return True


# ── Certificate inspection ────────────────────────────────────────────────────
def inspect_cert(path: Path, label: str) -> bool:
    """Parse and display certificate subject, issuer, and expiry."""
    if not HAS_CRYPTOGRAPHY:
        print(f"  {WARN}  {label}: install 'cryptography' for cert inspection")
        return True

    try:
        cert = x509.load_pem_x509_certificate(path.read_bytes(), default_backend())

        # Handle cryptography >=42.0.0 (timezone-aware) and older versions
        try:
            not_before = cert.not_valid_before_utc
            not_after = cert.not_valid_after_utc
        except AttributeError:
            not_before = cert.not_valid_before.replace(tzinfo=timezone.utc)
            not_after = cert.not_valid_after.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        days_left = (not_after - now).days

        print(f"      Subject : {cert.subject.rfc4514_string()}")
        print(f"      Issuer  : {cert.issuer.rfc4514_string()}")
        print(
            f"      Valid   : {not_before.strftime('%Y-%m-%d')} → "
            f"{not_after.strftime('%Y-%m-%d')}"
        )

        if now < not_before:
            print(f"  {FAIL}  {label}: certificate is not yet valid")
            return False
        if days_left < 0:
            print(f"  {FAIL}  {label}: expired {abs(days_left)} days ago")
            return False
        if days_left < 30:
            print(f"  {WARN}  {label}: expires in {days_left} days — renew soon")
        else:
            print(f"  {PASS}  {label}: valid for {days_left} more days")

        return True

    except Exception as exc:
        print(f"  {FAIL}  {label}: failed to parse certificate → {exc}")
        return False


# ── SSL context verification ──────────────────────────────────────────────────
def build_ssl_context(cfg: Config) -> Optional[ssl.SSLContext]:
    """Build the SSL context to catch mismatches before connecting."""
    print(f"\n{SEP}\n  SSL Context\n{SEP}")
    try:
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.check_hostname = cfg.verify_hostname

        if cfg.ca_cert:
            ctx.load_verify_locations(str(cfg.ca_cert))
            print(f"  {PASS}  CA certificate loaded into context")
        else:
            ctx.load_default_certs()
            print(f"  {WARN}  No CA cert provided — using system trust store")

        if cfg.certfile and cfg.keyfile:
            ctx.load_cert_chain(str(cfg.certfile), str(cfg.keyfile))
            print(f"  {PASS}  Client certificate and key matched successfully")
        elif cfg.certfile or cfg.keyfile:
            print(
                f"  {WARN}  Both --cfg.certfile and --cfg.keyfile must be supplied together"
            )

        return ctx

    except ssl.SSLError as exc:
        print(f"  {FAIL}  SSL context error: {exc}")
        return None
    except Exception as exc:
        print(f"  {FAIL}  Unexpected error building SSL context: {exc}")
        return None


# ── Live MQTT connection check ────────────────────────────────────────────────
async def check_mqtt_connection(cfg: Config) -> bool:
    """Attempt a live MQTT TLS connection and publish a test message."""
    print(f"\n{SEP}\n  MQTT Connection  ({cfg.broker}:{cfg.port})\n{SEP}")

    tls_params = aiomqtt.TLSParameters(
        ca_certs=str(cfg.ca_cert) if cfg.ca_cert else None,
        certfile=str(cfg.certfile) if cfg.certfile else None,
        keyfile=str(cfg.keyfile) if cfg.keyfile else None,
        cert_reqs=ssl.CERT_REQUIRED if cfg.verify_hostname else ssl.CERT_NONE,
    )

    try:
        async with aiomqtt.Client(
            hostname=cfg.broker,
            port=cfg.port,
            tls_params=tls_params,
            identifier=cfg.client_id,
            timeout=cfg.timeout,
        ) as client:
            print(f"  {PASS}  TLS handshake successful")
            print(f"  {PASS}  Connected to broker")
            await client.publish("tls_check/ping", payload="ok", qos=0)
            print(f"  {PASS}  Test publish succeeded")
            return True

    except aiomqtt.MqttError as exc:
        print(f"  {FAIL}  MQTT error:            {exc}")
    except ssl.SSLCertVerificationError as exc:
        print(f"  {FAIL}  Certificate verify failed: {exc}")
    except ssl.SSLError as exc:
        print(f"  {FAIL}  TLS handshake failed:  {exc}")
    except OSError as exc:
        print(f"  {FAIL}  Network/socket error:  {exc}")
    except Exception as exc:
        print(f"  {FAIL}  Unexpected error:      {exc}")

    return False


# ── Orchestrate all checks ────────────────────────────────────────────────────
async def run_checks(cfg: Config) -> bool:
    results: list[bool] = []

    # 1 ── File existence
    print(f"\n{SEP}\n  Certificate Files\n{SEP}")
    for path, label in [
        (cfg.ca_cert, "CA cert"),
        (cfg.certfile, "Client cert"),
        (cfg.keyfile, "Client key"),
    ]:
        results.append(check_file_exists(path, label))

    # 2 ── Certificate details (CA + client cert only, not the private key)
    print(f"\n{SEP}\n  Certificate Details\n{SEP}")
    for path, label in [
        (cfg.ca_cert, "CA cert"),
        (cfg.certfile, "Client cert"),
    ]:
        if path and path.exists():
            results.append(inspect_cert(path, label))

    # 3 ── SSL context build
    context = build_ssl_context(cfg)
    if context is None:
        results.append(False)
    else:
        # 4 ── Live broker connection
        results.append(await check_mqtt_connection(cfg))

    # ── Summary ───────────────────────────────────────────────────────────────
    all_passed = all(results)
    print(f"\n{'═' * 54}")
    if all_passed:
        print(f"  {PASS}  All checks passed")
    else:
        failed = results.count(False)
        print(f"  {FAIL}  {failed} check(s) failed")
    print(f"{'═' * 54}\n")

    return all_passed


# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> None:
    parser = ArgumentParser(
        description="Check TLS certificates against an MQTT broker",
        env_prefix="MQTT_TLS",
    )
    parser.add_dataclass_arguments(Config, "cfg")
    args = parser.parse_args()
    cfg: Config = parser.instantiate_classes(args).cfg

    print(f"\n{'═' * 54}")
    print("  MQTT TLS Certificate Checker")
    print(f"{'═' * 54}")
    print(f"  Broker          : {cfg.broker}:{cfg.port}")
    print(f"  CA cert         : {cfg.ca_cert or 'system defaults'}")
    print(f"  Client cert     : {cfg.certfile or 'none'}")
    print(f"  Client key      : {cfg.keyfile or 'none'}")
    print(f"  Verify hostname : {cfg.verify_hostname}")
    print(f"  Timeout         : {cfg.timeout}s")

    success = anyio.run(run_checks, cfg, backend="asyncio")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
