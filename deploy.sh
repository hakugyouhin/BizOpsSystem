#!/bin/bash
#
# BizOpsSystem - 高速デプロイスクリプト（Mac/Linux）
#
# 使用方法:
#   ./deploy.sh          → 確認プロンプト付きでデプロイ
#   ./deploy.sh --force  → 確認なしでデプロイ

set -e

# 設定
PROJECT_ID="bizopssystem"
IMAGE_NAME="bizopssystem"
REGION="asia-northeast1"
SERVICE_NAME="bizopssystem"
IMAGE_URI="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:latest"

echo ""
echo "===================================================="
echo "  BizOpsSystem - Cloud Run 高速デプロイ"
echo "===================================================="
echo ""
echo "設定:"
echo "  - プロジェクト: ${PROJECT_ID}"
echo "  - イメージ: ${IMAGE_URI}"
echo "  - サービス: ${SERVICE_NAME}"
echo "  - リージョン: ${REGION}"
echo ""

# ステップ 1: Docker イメージをビルド
echo "[1/3] Docker イメージをビルド中..."
docker build -t "${IMAGE_URI}" .
echo "✅ ビルド完了"
echo ""

# ステップ 2: Container Registry にプッシュ
echo "[2/3] Container Registry にプッシュ中..."
docker push "${IMAGE_URI}"
echo "✅ プッシュ完了"
echo ""

# ステップ 3: Cloud Run にデプロイ
if [ "$1" == "--force" ]; then
    CONFIRM="y"
else
    echo "[3/3] Cloud Run にデプロイします"
    echo ""
    read -p "確認: 本当にデプロイしますか？ (y/n): " CONFIRM
fi

if [ "$CONFIRM" == "y" ] || [ "$CONFIRM" == "Y" ]; then
    echo "デプロイ中..."
    gcloud run deploy "${SERVICE_NAME}" \
        --image "${IMAGE_URI}" \
        --region "${REGION}" \
        --platform managed \
        --allow-unauthenticated

    echo ""
    echo "✅ デプロイ完了！"
    echo ""
    echo "サービス URL:"
    gcloud run services describe "${SERVICE_NAME}" \
        --region "${REGION}" \
        --format='value(status.url)'
else
    echo "❌ デプロイをキャンセルしました"
    exit 1
fi

echo ""
echo "===================================================="
echo "次のステップ:"
echo "  git add . && git commit -m \"feat: xxx\" && git push origin main"
echo "（GitHub 履歴を記録して、Cloud Build バックアップ実行）"
echo "===================================================="
echo ""
