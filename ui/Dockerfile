FROM python:3.11-slim

ARG VERSION=0.0.0
ENV APP_VERSION=${VERSION}

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .
# Write version to file for app to read
RUN echo "${VERSION}" > VERSION

EXPOSE 8501

RUN useradd --create-home appuser
USER appuser

CMD ["streamlit", "run", "app.py"]
