FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV HF_HOME=/home/appuser/.cache/huggingface

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

RUN useradd -m -u 10001 -s /usr/sbin/nologin appuser

COPY --chown=appuser:appuser . .
RUN mkdir -p /app/chroma_db /home/appuser/.cache/huggingface \
    && chown -R appuser:appuser /app /home/appuser

USER appuser

CMD ["python", "-m", "agents.draft_graph"]