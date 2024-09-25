# AI電話システム

このリポジトリは、AIを利用して電話対応を行うシステムの設定および運用手順を提供します。このシステムは、vocode、Twilio、Deepgram、OpenAI、Eleven Labsなどのサービスを利用して構築されています。

## 環境設定

1. `/phonecall/.env.sample`をコピーし、ファイル名を`.env`に変更します。
2. `.env`ファイル内の必要な情報をすべて埋めます。

```plaintext
# BASE_URL: サーバーのURL。例: telephony-app.ngrok.io
BASE_URL=b45f-60-111-24-187.ngrok-free.app

# Deepgram APIキー: 音声認識に使用
DEEPGRAM_API_KEY="あなたのDeepgram APIキー"

# OpenAI APIキー: 自然言語処理に使用
OPENAI_API_KEY="あなたのOpenAI APIキー"

# TwilioアカウントSID: Twilio APIリクエストに使用
TWILIO_ACCOUNT_SID="あなたのTwilioアカウントSID"

# Twilio認証トークン: Twilio APIリクエストに使用
TWILIO_AUTH_TOKEN="あなたのTwilio認証トークン"
```

## Twilio設定

Twilioで取得した電話番号に対して、Webhook HTTP POSTを設定します。設定手順は以下の通りです：

1. Twilioコンソールにログインし、対象の電話番号を選択します。
2. "A Call Comes In"セクションで、Webhook URLに立てたサーバーのURLに`/inboundcall`を追加したものを入力します。例: `https://your-server-url.com/inboundcall`
3. .envファイルの`BASE_URL`にも、上記のWebhook URLを設定します。TwilioがこのURLにWebSocketを接続してきます。

## サーバーの立ち上げ

サーバーを立ち上げるには、以下の手順に従います：

1. Dockerイメージをビルドします。
   ```sh
   docker build -t vocode-telephony-app .
   ```
2. Docker Composeを使用してサーバーを立ち上げます。
   ```sh
   docker compose up
   ```

## カスタマイズ

システムをカスタマイズするには、以下の手順を参考にしてください：

1. **プロンプト、第一声、フィラーの変更**：
   - `main.py`内の該当する定数を編集します。具体的には、`INITIAL_MESSAGE`、`PROMPT`、および`FILLER_WORDS`を編集します。

2. **Eleven Labsのカスタムボイスを使用**：
   - `VolumeAdjustableElevenLabsSynthesizerConfig`の`voice_id`を設定します。
   - カスタムボイスを使用する際に音量が小さくなることがあります。この場合は、`volume_factor`を調整して音量を適切に設定します。

例：
```python
synthesizer_config=VolumeAdjustableElevenLabsSynthesizerConfig.from_telephone_output_device(
    api_key=os.environ["ELEVEN_LABS_API_KEY"],
    model_id="eleven_multilingual_v2",
    volume_factor=1.2,  # 必要に応じて調整
    voice_id="あなたのカスタムボイスID",
),
```