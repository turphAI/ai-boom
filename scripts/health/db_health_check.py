#!/usr/bin/env python3
"""
Database Health Check Script
Monitors the health of the PlanetScale database endpoint by verifying TCP connectivity.

Notes:
- Avoids ORM/application imports to keep this script self-contained for CI runners.
- Loads .env if present. If DATABASE_URL is missing, exits successfully with a warning to avoid false negatives.
"""

import os
import sys
import socket
from datetime import datetime
from urllib.parse import urlparse


def load_env_file_if_present() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        pass


def parse_mysql_url(database_url: str):
    parsed = urlparse(database_url)
    # Support mysql or mysql+pymysql schemes
    if parsed.scheme.startswith("mysql") is False:
        return None

    host = parsed.hostname or ""
    port = parsed.port or 3306
    return host, port


def check_tcp_connectivity(host: str, port: int, timeout_seconds: int = 5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except Exception:
        return False


def main():
    print(f"🗄️  Starting database health check at {datetime.now()}")

    load_env_file_if_present()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("⚠️  DATABASE_URL not set; skipping DB connectivity check.")
        # Do not fail the workflow if DB is not configured for this environment
        sys.exit(0)

    parsed = parse_mysql_url(database_url)
    if not parsed:
        print("⚠️  DATABASE_URL is not a MySQL URL; skipping DB connectivity check.")
        sys.exit(0)

    host, port = parsed
    print(f"🔍 Checking TCP connectivity to {host}:{port}...")

    if not host:
        print("❌ Could not determine database host from DATABASE_URL")
        sys.exit(1)

    if check_tcp_connectivity(host, port):
        print("✅ Database endpoint is reachable via TCP")
        sys.exit(0)
    else:
        print("❌ Could not reach database endpoint via TCP")
        sys.exit(1)


if __name__ == "__main__":
    main()
