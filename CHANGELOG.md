# Changelog

## 2.6.2-railway.1 (2026-11-24)

First release of the Railway template.

* django-helpdesk 2.6.2 (PyPI, hash-locked) with Django 6.1.3 and gunicorn 27.0.1 on `python:3.15.2-slim-trixie@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928`.
* Railway PostgreSQL for data, Railway Bucket for attachments.
* Admin account and Django secret key generated per deploy; django-axes login throttling.
* Health check `/healthz`; mailbox poll every 60 s; non-zero exit on crash.
