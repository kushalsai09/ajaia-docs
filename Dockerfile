FROM python:3.12-slim
WORKDIR /app
COPY app.py index.html styles.css script.js ./
ENV PORT=8000 DATABASE_PATH=/data/docs.sqlite3 PYTHONUNBUFFERED=1
RUN mkdir -p /data
EXPOSE 8000
CMD ["python", "app.py"]
