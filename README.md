# aws-jp-blog-feed-notifier

AWS公式ブログ（日本 / News）のRSSフィードから「前日に公開された記事」を取得してDynamoDBへ保存し、DynamoDB Streamsで起動されたLambdaがWebhookへ通知します。

## 何ができる？

- RSS: https://aws.amazon.com/jp/blogs/news/feed/ を取得
- JST基準で「前日」の記事だけ抽出してDynamoDBへ保存（title / url / excerpt）
- DynamoDB Streams（NEW_IMAGE）で notifier Lambda を起動
- notifier が SSM Parameter Store の `/Blog/Webhook` からWebhook URLを取得し、`{"title","text","url"}` をPOST

## 構成

- Teams: Microsoft TeamsのチャネルでWebhook URLを発行
- crawler Lambda: [src/lambda/crawl_rss_feed.py](src/lambda/crawl_rss_feed.py)
	- `BLOG_POSTS_TABLE`（DynamoDB）へ書き込み
- notifier Lambda: [src/lambda/notifier.py](src/lambda/notifier.py)
	- Streamsイベントの `NewImage` から `{title,url,excerpt}` を取り出してWebhookへ送信
- DynamoDB: Streams有効（`NEW_IMAGE`）
- EventBridge Scheduler: crawler定期起動
	- デフォルトでは **DISABLED**（有効化手順は後述）

Terraform構成は [terraform/](terraform/) 配下にあります。

## 前提

- macOS / Linux（Windowsでも可）
- Terraform（1.5+）
- AWS認証情報（`AWS_PROFILE` or 環境変数）
- Python 3.12+
- uv（任意。ローカルでPythonを動かす場合）

## デプロイ（Terraform）

### 1) backend（state用S3/DynamoDB）を作成

backendスタックは [terraform/backend/](terraform/backend/) にあります。

```bash
cd terraform/backend
terraform init
terraform apply
```

出力された `bucket` / `dynamodb_table` を、[terraform/main.tf](terraform/main.tf) の `backend "s3"` に反映してください。

### 2) アプリ本体をデプロイ

```bash
cd terraform
terraform init
terraform apply
```

## Webhook URL（SSM Parameter）

notifier Lambda は `/Blog/Webhook` を `WithDecryption=true` で取得します。

例（SecureStringで作る場合）:

```bash
aws ssm put-parameter \
	--name "/Blog/Webhook" \
	--type "SecureString" \
	--value "https://your-webhook.example" \
	--overwrite
```

※ Terraform側の権限は現在 `ssm:GetParameter` / `kms:Decrypt` が広め（`*`）です。必要なら後で最小権限に絞れます。

## スケジュールを有効化する

EventBridge Scheduler は、初期状態で無効（DISABLED）になるようにしてあります。
有効化したい場合は [terraform/eventbridge.tf](terraform/eventbridge.tf) の `schedules.lambda-cron.state` を `true` にして `terraform apply` してください。

## Webhook送信のテスト

### Lambdaコンソールでテストイベントを流す

テスト用の DynamoDB Streams 形式イベントを用意しています:

- [test-events/notifier-dynamodb-insert.json](test-events/notifier-dynamodb-insert.json)

AWSコンソール → Lambda（notifier）→ テスト → 新規イベント作成 → 上記JSONを貼り付けて実行。

### CLIで notifier Lambda を直接 invoke

```bash
aws lambda invoke \
	--function-name "<notifierのLambda関数名>" \
	--payload fileb://test-events/notifier-dynamodb-insert.json \
	out.json
cat out.json
```

## トラブルシュート

- Webhookに届かない
	- notifier のCloudWatch Logsを確認（SSM取得失敗、Webhook側エラー等）
	- `/Blog/Webhook` が存在するか、値が正しいか確認
- crawler が記事を保存しない
	- JSTの「前日」判定のため、実行時刻によっては件数0がありえます
	- RSS側の `pubDate` が取得できているか確認
