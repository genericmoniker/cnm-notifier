# cnm-notifier dockerfile

FROM python:3.12-slim-bullseye

RUN useradd --create-home appuser
WORKDIR /home/appuser

RUN export DEBIAN_FRONTEND=noninteractive && \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y --no-install-recommends tini && \
  apt-get -y clean && \
  rm -rf /var/lib/apt/lists/*

USER appuser

# Create a virtual environment.
ENV VIRTUAL_ENV=/home/appuser/.venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies.
COPY --chown=appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium for Playwright.
USER root
RUN playwright install-deps chromium
USER appuser
RUN playwright install chromium

COPY --chown=appuser . .

ENTRYPOINT ["tini", "--", "python3", "main.py"]
# To debug the container: ENTRYPOINT ["tail", "-f", "/dev/null"]
