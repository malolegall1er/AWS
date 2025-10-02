# Dockerfile
FROM python:3.11-slim

# OS deps
RUN apt-get update && apt-get install -y --no-install-recommends \ 
    git curl ca-certificates &&     rm -rf /var/lib/apt/lists/*

# App
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py /app/
COPY templates /app/templates
COPY static /app/static

# workspace for uploads/repos
RUN mkdir -p /workspace/uploads /workspace/repos
ENV WORKSPACE=/workspace

# Flask listen
ENV FLASK_APP=app.py
EXPOSE 8080

CMD ["python", "app.py"]
