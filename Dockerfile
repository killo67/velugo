FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx cron gettext-base \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

# Nginx config (port injected at container startup via envsubst)
COPY docker/nginx.conf.template /etc/nginx/conf.d/default.conf.template

# Static site
COPY src /app/src
COPY assets /app/assets

# Pipeline scripts
COPY scripts /app/scripts

WORKDIR /app

# Cron: 6:30 AM IST = 1:00 AM UTC
RUN echo '0 1 * * * root bash -c "source /app/.docker-env && cd /app && bash scripts/run-daily.sh" >> /var/log/newagg.log 2>&1' \
    > /etc/cron.d/newagg \
    && chmod 644 /etc/cron.d/newagg

COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80

CMD ["/start.sh"]
