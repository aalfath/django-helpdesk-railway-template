# Deploy and Host Django Helpdesk on Railway

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

## Why Deploy Django Helpdesk on Railway?

<!-- Recommended: Keep this section as shown below -->
Railway is a singular platform to deploy your infrastructure stack. Railway will host your infrastructure so you don't have to deal with configuration, while allowing you to vertically and horizontally scale it.

By deploying Django Helpdesk on Railway, you are one step closer to supporting a complete full-stack application with minimal burden. Host your servers, databases, AI agents, and more on Railway.
<!-- End recommended section -->
