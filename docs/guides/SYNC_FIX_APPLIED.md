# 同期機能の修正完了

## 問題の原因

**CORSエラー:** バックエンドのCORS設定がフロントエンドのポート（3010）を許可していなかったため、ブラウザがAPIリクエストをブロックしていました。

## 修正内容

### 1. CORS設定の更新

**ファイル:** [backend/app/core/config.py:58](backend/app/core/config.py#L58)

```python
# 修正前
CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

# 修正後
CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3010", "http://localhost:8000"]
```

### 2. 同期ページのパス表示を更新

**ファイル:** [frontend/app/sync/page.tsx:184-185](frontend/app/sync/page.tsx#L184-L185)

ネットワークパスから実際の使用パスに変更:
- 従業員: `E:\BASEDATEJP\【新】社員台帳(UNS)T　2022.04.05～.xlsm`
- 工場: `E:\BASEDATEJP\factories_index.json`

## 確認方法

1. http://localhost:3010/sync にアクセス
2. 以下のボタンをクリック:
   - **従業員を同期** - 従業員データを同期
   - **工場を同期** - 工場データを同期
   - **すべて同期** - 両方を同期

3. 成功時は以下の緑色のメッセージが表示されます:
   ```
   ✅ 同期成功
   従業員:
     処理済み: XXX
     新規作成: XXX
     更新: XXX
   ```

## 現在のデータベース状態

```
従業員: 785名（在籍: 334名、退社: 451名）
工場: 11社
ライン: 71ライン
```

## 技術詳細

### エラーの原因
- ブラウザのセキュリティポリシー（CORS）により、異なるオリジンからのAPIリクエストがブロックされる
- フロントエンド: `http://localhost:3010`
- バックエンド: `http://localhost:8010`
- CORS設定に `localhost:3010` が含まれていなかったため、リクエストが拒否された

### 修正後の動作
- バックエンドが `Access-Control-Allow-Origin: http://localhost:3010` ヘッダーを返す
- ブラウザがリクエストを許可
- 同期機能が正常に動作

## 次のステップ

同期機能が正常に動作することを確認した後:
1. 定期的な同期スケジュールの設定（将来の機能）
2. 自動同期の実装（cron jobまたはスケジューラー）
3. 同期履歴の記録

## トラブルシューティング

もし再び「Network Error」が出る場合:

1. **バックエンドのログを確認:**
   ```bash
   docker logs uns-kobetsu-backend --tail 50
   ```

2. **ブラウザのコンソールを確認:**
   - F12を押してDevToolsを開く
   - Console タブでエラーメッセージを確認
   - Network タブでリクエストの詳細を確認

3. **CORS設定を確認:**
   ```bash
   curl -X GET http://localhost:8010/api/v1/sync/status \
     -H "Origin: http://localhost:3010" -i
   ```
   レスポンスに `access-control-allow-origin: http://localhost:3010` が含まれていることを確認
