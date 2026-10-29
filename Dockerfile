FROM python:3.13-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# without tzdata the container is stuck on UTC, which shifts the notification
# quiet hours and every timestamp shown to users - run with e.g. -e TZ=Europe/Warsaw
RUN apk add --no-cache tzdata

RUN mkdir -p /app/data
RUN mkdir -p /app/data/profile_pics

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# non-root user
RUN adduser -D librusik && \
    chown -R librusik:librusik /app

USER librusik

CMD ["python", "librusik.py", "--skip-wizard"]