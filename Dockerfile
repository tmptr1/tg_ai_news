FROM python:3.12-alpine
ENV PYTHONUNBUFFERED=1
WORKDIR /tg_ai_news_dir
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENTRYPOINT ["python", "main.py"]