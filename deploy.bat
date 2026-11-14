@echo off
REM BizOpsSystem - 高速デプロイスクリプト
REM
REM 使用方法:
REM   deploy.bat          → 確認プロンプト付きでデプロイ
REM   deploy.bat --force  → 確認なしでデプロイ

setlocal enabledelayedexpansion

REM 設定
set PROJECT_ID=bizopssystem
set IMAGE_NAME=bizopssystem
set REGION=asia-northeast1
set SERVICE_NAME=bizopssystem

REM Docker イメージの URI
set IMAGE_URI=gcr.io/%PROJECT_ID%/%IMAGE_NAME%:latest

echo.
echo ====================================================
echo   BizOpsSystem - Cloud Run 高速デプロイ
echo ====================================================
echo.
echo 設定:
echo   - プロジェクト: %PROJECT_ID%
echo   - イメージ: %IMAGE_URI%
echo   - サービス: %SERVICE_NAME%
echo   - リージョン: %REGION%
echo.

REM ステップ 1: Docker イメージをビルド
echo [1/3] Docker イメージをビルド中...
docker build -t %IMAGE_URI% .
if errorlevel 1 (
    echo ❌ Docker ビルドに失敗しました
    exit /b 1
)
echo ✅ ビルド完了
echo.

REM ステップ 2: Container Registry にプッシュ
echo [2/3] Container Registry にプッシュ中...
docker push %IMAGE_URI%
if errorlevel 1 (
    echo ❌ プッシュに失敗しました
    exit /b 1
)
echo ✅ プッシュ完了
echo.

REM ステップ 3: Cloud Run にデプロイ
if "%1"=="--force" (
    set CONFIRM=y
) else (
    echo [3/3] Cloud Run にデプロイします
    echo.
    set /p CONFIRM="確認: 本当にデプロイしますか？ (y/n): "
)

if /i "%CONFIRM%"=="y" (
    echo デプロイ中...
    gcloud run deploy %SERVICE_NAME% ^
        --image %IMAGE_URI% ^
        --region %REGION% ^
        --platform managed ^
        --allow-unauthenticated

    if errorlevel 1 (
        echo ❌ デプロイに失敗しました
        exit /b 1
    )

    echo.
    echo ✅ デプロイ完了！
    echo.
    echo サービス URL:
    gcloud run services describe %SERVICE_NAME% ^
        --region %REGION% ^
        --format='value(status.url)'
) else (
    echo ❌ デプロイをキャンセルしました
    exit /b 1
)

echo.
echo ====================================================
echo 次のステップ:
echo   git add . ^& git commit -m "feat: xxx" ^& git push origin main
echo （GitHub 履歴を記録して、Cloud Build バックアップ実行）
echo ====================================================
echo.
