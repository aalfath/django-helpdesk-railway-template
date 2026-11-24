#!/bin/sh
# Start Django Helpdesk on Railway: setup, then gunicorn, plus a 60 s mailbox poll
# (upstream's dockerized image runs `manage.py get_email` from cron every minute).
# Exits non-zero if gunicorn stops unexpectedly, so Railway's ON_FAILURE policy restarts it.
set -eu
cd /app

# CPUs from the cgroup limit, not the host (Railway shows 32+ host CPUs).
cpus=1
if [ -r /sys/fs/cgroup/cpu.max ]; then
  read -r quota period < /sys/fs/cgroup/cpu.max || true
  if [ "${quota:-max}" != "max" ] && [ "${period:-0}" -gt 0 ]; then
    cpus=$(( (quota + period - 1) / period ))
  fi
fi
[ "$cpus" -ge 1 ] || cpus=1
workers=${GUNICORN_WORKERS:-$(( cpus + 1 ))}
[ "$workers" -gt 4 ] && [ -z "${GUNICORN_WORKERS:-}" ] && workers=4
[ "$workers" -lt 2 ] && workers=2
threads=${GUNICORN_THREADS:-4}
port=${PORT:-8000}

python /app/bootstrap.py

gunicorn helpdesk_site.wsgi:application \
  --bind "[::]:${port}" \
  --workers "$workers" --threads "$threads" --worker-class gthread \
  --timeout "${GUNICORN_TIMEOUT:-60}" --graceful-timeout 10 \
  --max-requests 1000 --max-requests-jitter 100 \
  --preload --access-logfile - --error-logfile - --log-level warning \
  --forwarded-allow-ips '*' &
gpid=$!
echo "[start] gunicorn pid $gpid on port $port ($workers workers x $threads threads, $cpus CPU)"

stop() { kill -TERM "$gpid" 2>/dev/null || true; wait "$gpid" 2>/dev/null || true; exit 0; }
trap stop TERM INT

poll=${HELPDESK_EMAIL_POLL_SECONDS:-60}
elapsed=0
while kill -0 "$gpid" 2>/dev/null; do
  sleep 5 &
  wait $! || true
  elapsed=$(( elapsed + 5 ))
  if [ "$poll" -gt 0 ] && [ "$elapsed" -ge "$poll" ]; then
    elapsed=0
    python -m django get_email --quiet >/dev/null 2>&1 || echo "[start] get_email failed (check the queue's mailbox settings)"
  fi
done
wait "$gpid" 2>/dev/null && rc=0 || rc=$?
echo "[start] gunicorn exited (code $rc); exiting so Railway restarts the service"
[ "$rc" -eq 0 ] && rc=1
exit "$rc"
