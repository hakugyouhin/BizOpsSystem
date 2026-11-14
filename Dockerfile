FROM python:3.9-slim

# 作業ディレクトリ
WORKDIR /app

# LibreOffice インストール
RUN apt-get update && \
    apt-get install -y libreoffice && \
    rm -rf /var/lib/apt/lists/*

# Python 依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード
COPY . .

# ポート指定
ENV PORT=8080
EXPOSE 8080

# アプリケーション起動
CMD ["python", "app.py"]
