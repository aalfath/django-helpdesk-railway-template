# Django Helpdesk 2.6.2 for Railway.
# Upstream publishes no versioned image (djangohelpdesk/standalone only has `latest`
# and date tags, last built 2026-06), so we install the released, hash-locked
# PyPI package django-helpdesk==2.6.2 on a pinned official Python image.
FROM python:3.15.2-slim-trixie@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=helpdesk_site.settings \
    PYTHONPATH=/app

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --require-hashes --only-binary :all: -r /app/requirements.txt

COPY app/ /app/
RUN chmod 755 /app/start.sh \
 && DJANGO_HELPDESK_SECRET_KEY=build-only python -m django collectstatic --noinput -v 0 \
 && useradd --system --uid 10001 --home-dir /app --shell /usr/sbin/nologin helpdesk \
 && mkdir -p /data/media && chown -R helpdesk /data

USER helpdesk
EXPOSE 8000
CMD ["/app/start.sh"]
