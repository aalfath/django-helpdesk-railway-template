"""First-boot and every-boot setup for Django Helpdesk on Railway.

1. Wait until Postgres answers (a sibling's private DNS can lag on first deploy).
2. Take a Postgres advisory lock (overlapping Railway deploys must not migrate twice).
3. Apply migrations, quietly.
4. Create the admin from DJANGO_SUPERUSER_* if no user with that name exists
   (never resets a password that was changed in the UI).
5. Point the Django Site at the Railway public domain (used in e-mail links).
6. On an empty helpdesk, create one "Support" queue so tickets can be filed at once.
Exits non-zero on failure so Railway restarts the deployment.
"""
import os
import sys
import time

import django

django.setup()

from django.core.management import call_command  # noqa: E402
from django.db import connection  # noqa: E402
from django.db.utils import OperationalError  # noqa: E402

LOCK_ID = 7309201  # arbitrary, fixed for this template


def log(msg):
    print(f"[bootstrap] {msg}", flush=True)


def wait_for_db(timeout=180):
    deadline = time.monotonic() + timeout
    while True:
        try:
            connection.ensure_connection()
            return
        except OperationalError as exc:
            if time.monotonic() > deadline:
                log(f"database not reachable after {timeout}s: {exc}")
                sys.exit(1)
            log("waiting for the database...")
            time.sleep(3)
            connection.close()


def with_lock(fn, timeout=600):
    deadline = time.monotonic() + timeout
    with connection.cursor() as cur:
        while True:
            cur.execute("SELECT pg_try_advisory_lock(%s)", [LOCK_ID])
            if cur.fetchone()[0]:
                break
            if time.monotonic() > deadline:
                log("could not get the setup lock")
                sys.exit(1)
            log("another deploy is running setup, waiting...")
            time.sleep(3)
    try:
        fn()
    finally:
        with connection.cursor() as cur:
            cur.execute("SELECT pg_advisory_unlock(%s)", [LOCK_ID])


def setup():
    call_command("migrate", interactive=False, verbosity=0)
    log("migrations applied")

    from django.contrib.auth import get_user_model

    User = get_user_model()
    username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin").strip() or "admin"
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
    if not User.objects.filter(username=username).exists():
        if len(password) < 12:
            log("DJANGO_SUPERUSER_PASSWORD must be set (12+ characters) to create the admin")
            sys.exit(1)
        User.objects.create_superuser(username=username, email=email, password=password)
        log(f"created admin user '{username}'")
    else:
        log(f"admin user '{username}' already exists (password left unchanged)")

    domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if domain:
        from django.contrib.sites.models import Site

        Site.objects.update_or_create(id=1, defaults={"domain": domain, "name": "Django Helpdesk"})

    from helpdesk.models import Queue

    if not Queue.objects.exists():
        Queue.objects.create(title="Support", slug="support", allow_public_submission=False)
        log("created the default 'Support' queue")


if __name__ == "__main__":
    wait_for_db()
    with_lock(setup)
    log("setup complete")
