# Cloud Run 対応ガイド - 見積書作成機能

## 🎯 目標
Cloud Run で見積書作成機能を完全に動作させる

---

## 📋 **Step 1: Google Drive フォルダ ID を取得**

### 手順

1. **Google Drive にアクセス**
   ```
   https://drive.google.com
   ```

2. **見積書ファイルが保存されているフォルダを開く**
   ```
   例: G:\マイドライブ\96_tmp\20261010\
       ↓
   Google Drive 内の同じフォルダ
   ```

3. **フォルダのリンクをコピー**
   ```
   フォルダを右クリック → 「リンクをコピー」
   ```

4. **URL からフォルダ ID を抽出**
   ```
   コピーされた URL:
   https://drive.google.com/drive/folders/1QaB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV

   フォルダ ID:
   1QaB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV
   ↑ これをコピーして保存
   ```

---

## 🔧 **Step 2: Cloud Run に環境変数を設定**

### Google Cloud Console で設定

1. **Google Cloud Console を開く**
   ```
   https://console.cloud.google.com
   ```

2. **Cloud Run → bizopssystem サービスを開く**

3. **編集ボタンをクリック**

4. **環境変数を追加**

   ```
   【追加する環境変数】
   
   名前: DRIVE_MANAGEMENT_FOLDER_ID
   値: [取得したフォルダ ID を貼り付け]
   
   名前: DRIVE_PRICE_LIST_FOLDER_ID
   値: [取得したフォルダ ID を貼り付け]
   （両方同じフォルダなら同じ ID でOK）
   ```

5. **デプロイボタンをクリック**
   ```
   デプロイが完了するまで待機（2～3分）
   ```

---

## 🚀 **Step 3: Cloud Run で見積書作成を実行**

### Web UI での入力方法

```
URL: https://bizopssystem-855712749718.asia-northeast1.run.app/estimate
```

#### **ステップ②：管理ファイル&金額リストを指定**

**管理ファイル入力欄:**
```
1QaB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV
（Google Drive フォルダ ID）
```

**金額リスト入力欄:**
```
1QaB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV
（同じフォルダ ID で OK）
```

#### **ステップ③：見積書格納フォルダを指定**

**フォルダパス:**
```
output
（Cloud Run 内の一時フォルダ）
```

#### **ステップ④⑤：見積書作成**

「見積内容作成」ボタン → 「見積書作成」ボタン → 「PDF見積書作成」ボタン

---

## ✅ **確認チェックリスト**

- [ ] Google Drive フォルダ ID を取得した
- [ ] Cloud Console で環境変数を設定した
- [ ] Cloud Run のデプロイが完了した（ビルド履歴で確認）
- [ ] Cloud Run URL で見積書ページを開いた
- [ ] フォルダ ID を入力して「見積内容作成」をクリック
- [ ] ✅ メッセージが表示されたら成功

---

## 🔴 **トラブルシューティング**

### エラー: "ファイルが見つかりません"

**原因:** Google Drive フォルダに指定のファイルがない

**解決策:**
1. Google Drive フォルダを確認
2. 以下のファイルが存在するか確認：
   - `請求書＆注文書生成_双日用_Excel版2.xlsx`
   - `派遣業務管理台帳_統合.xlsx`
3. ファイル名が完全一致しているか確認

### エラー: "Google Drive API が初期化できません"

**原因:** サービスアカウントの認証が失敗

**解決策:**
1. Cloud Run の権限を確認
2. サービスアカウントが Google Drive API へのアクセス権を持つか確認
3. Cloud Console → IAM で確認

---

## 💾 **ローカル開発との使い分け**

| 環境 | 管理ファイル入力 | 金額リスト入力 |
|------|---------|---------|
| **Flask（ローカル）** | `G:\...` | `G:\...` |
| **Cloud Run** | Google Drive フォルダ ID | Google Drive フォルダ ID |

---

## 📊 **動作フロー**

```
ユーザーが Cloud Run で見積書ページを開く
    ↓
フォルダ ID を入力 → 「見積内容作成」
    ↓
1️⃣ API が Google Drive フォルダ ID を受け取る
2️⃣ Google Drive API でファイルを検索
3️⃣ ファイルを一時フォルダにダウンロード
4️⃣ Excel に見積データを書き込み
    ↓
✅ 見積内容が作成される
```

---

## 🔗 **関連ドキュメント**

- DEVELOPMENT.md - 開発ガイド
- deploy.bat / deploy.sh - デプロイスクリプト
- utils/drive_utils.py - Google Drive API ユーティリティ
- routes/api.py - API エンドポイント

---

**🎉 これで Cloud Run で見積書作成が動作します！**
