[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/new/template/django-helpdesk?utm_medium=integration&utm_source=button&utm_campaign=django-helpdesk)

# Django Helpdesk on Railway

Django Helpdesk is an open-source ticket tracker built on Django. Staff work tickets in queues with priorities, assignment, follow-ups, attachments, a Kanban board and a knowledge base, while customers can file and follow tickets through a public web form or by e-mail. It is BSD-3-Clause licensed and maintained since 2008.

## About Hosting Django Helpdesk

This template deploys django-helpdesk 2.6.2 (Django 6.1, gunicorn) built from a public GitHub repo, a Railway PostgreSQL database and a Railway Bucket for ticket attachments. On first boot the app applies its migrations, creates the admin account from generated variables, points e-mail links at your Railway domain and adds a "Support" queue. Log in at `/login/` as `admin` with the `DJANGO_SUPERUSER_PASSWORD` shown in the app service's Variables tab, then add staff users and queues under `/admin/`. E-mail is off until you add SMTP variables. Updates ship as GitHub commits, so Railway offers each new version as an update you apply when ready.

## Common Use Cases

* An internal IT or facilities helpdesk with queues per team
* Customer support tickets from a public web form and a support mailbox
* A small knowledge base of answers next to the ticket queue

## Dependencies for Django Helpdesk Hosting

* PostgreSQL (Railway's PostgreSQL service, on its own volume)
* A Railway Bucket (S3-compatible storage for ticket attachments)

### Deployment Dependencies

* [django-helpdesk on GitHub](https://github.com/django-helpdesk/django-helpdesk) and its [v2.6.2 release](https://github.com/django-helpdesk/django-helpdesk/releases/tag/v2.6.2)
* [django-helpdesk documentation](https://django-helpdesk.readthedocs.io/)
* [Template repo](https://github.com/aalfath/django-helpdesk-railway-template)

### Implementation Details

Services: **Django Helpdesk** (the web app, public, health check `/healthz`; it also checks queue mailboxes every 60 seconds the way upstream's cron job does), **Postgres** (tickets, users, settings) and **Bucket** (attachments, served as downloads through short-lived signed links).

What you get on top of upstream's Docker setup:

* No default password: the admin password and Django secret key are generated per deploy, and the admin is created only if it doesn't exist, so a password you change later is never reset.
* Login throttling with django-axes (10 failed attempts per username and IP locks that pair for 15 minutes), which upstream leaves to the deployer.
* Fits Railway's Free plan: about 190 MB of RAM in use at a 0.5 GB limit, worker count taken from the service's CPU limit, and a crash makes the service exit with an error so Railway restarts it.

Optional variables on the Django Helpdesk service:

* E-mail: `EMAIL_HOST`, `EMAIL_PORT` (587), `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` (True), `DEFAULT_FROM_EMAIL`. Incoming mail is set per queue in `/admin/` (POP3/IMAP).
* Public portal: `HELPDESK_SUBMIT_A_TICKET_PUBLIC` and `HELPDESK_VIEW_A_TICKET_PUBLIC` (True); set them to False for staff-only use. Public submission is also off per queue until you tick "Allow public submission".
* `HELPDESK_REDIRECT_TO_LOGIN_BY_DEFAULT`, `HELPDESK_KANBAN_ENABLED`, `HELPDESK_KB_ENABLED`, `HELPDESK_API_ENABLED`, `TZ`.

## Repo layout and updates

* `Dockerfile`: pinned `python:3.15.2-slim-trixie@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928`, installing the hash-locked `requirements.txt` (django-helpdesk 2.6.2 from PyPI, Django 6.1.3, gunicorn 27.0.1, django-axes 9.1.0, django-storages 1.14.6). Upstream's `djangohelpdesk/standalone` image publishes only `latest` and date tags, so we pin the released PyPI package instead.
* `app/helpdesk_site/`: Django settings (Railway Postgres through `DATABASE_URL`, Railway Bucket through the `AWS_*` variables, local disk at `/data/media` if no bucket is set), URLs and the `/healthz` endpoint.
* `app/bootstrap.py`: waits for Postgres, runs migrations under an advisory lock, creates the admin once, sets the Site domain, adds the first queue.
* `app/start.sh`: starts gunicorn (workers from the cgroup CPU limit) and the 60-second mailbox poll; exits non-zero if gunicorn dies.
* `compose.test.yml`: local test stack only (Railway doesn't use it).

Updates: we bump the pins here and note them in `CHANGELOG.md`. Each merge to `main` makes Railway show an "update available" notice on your deployment; read the changelog, then apply it. Migrations run on start.

Variables set by the template (Django Helpdesk service): `PORT=8000`, `DATABASE_URL=${{Postgres.DATABASE_URL}}`, `DJANGO_HELPDESK_SECRET_KEY` and `DJANGO_SUPERUSER_PASSWORD` (generated), `DJANGO_SUPERUSER_USERNAME=admin`, and the five `AWS_*` references to the Bucket.
