# ========= Base =========
FROM python:3.11.7-slim

# ========= Env =========
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /SilentXBotz


# ========= System deps (single layer, fast) =========
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    mediainfo \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*


# ========= Python deps (cache optimized) =========
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ========= Copy project =========
COPY . .


# ========= Healthcheck (safe, optional but useful for Koyeb) =========
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
CMD python -c "print('ok')" || exit 1


# ========= Start =========
CMD ["python", "bot.py"]
