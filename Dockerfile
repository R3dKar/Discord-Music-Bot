FROM python:3.14.0-alpine3.22

WORKDIR /app
RUN apk add --no-cache ffmpeg opus && \
    addgroup -S botuser && \
    adduser -S botuser -G botuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R botuser:botuser .
USER botuser
CMD ["python", "main.py"]
