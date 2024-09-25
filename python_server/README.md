## 環境構築と動作確認

### 依存パッケージのインストール

```
poetry install
```

### 環境変数の設定
   以下のコマンドを実行し、環境変数を設定してください。
   各 API キーについては、それぞれのサービスで取得してください。
    * Google AI StudioのAPIキー(Vertex経由ではなくGoogle AI Studioを経由します)
    * Google Application Credential, Google Drive ID(ログを転送する機能を利用する場合必要となります)
    * Azure Text to SpeechのAPIキー
    * ELEVENLABSのAPIキー(声質変換を利用する場合)

```
cp .env.example .env
```

### YouTube のコメントを保存しておくDB作成(PostgreSQL(Docker))

```
make up
make db/reset
```

###  サンプル画像のダウンロード

PDF(を画像化した)ファイルを取得します。

```
poetry run python -m src.cli.import_pdf
poetry run python -m src.cli.import_docs_csv
```

###  知識 DB 作成

```
poetry run python -m src.cli.save_faiss_knowledge_db
poetry run python -m src.cli.save_faiss_db
```

###  RAG の評価

```
poetry run python -m src.cli.save_faiss_db --for-eval  # 評価する際はtrain/test split用に --for-eval オプションを追加
poetry run python -m src.cli.rag_evaluation.evaluate
```


### 対話のテスト

```

curl -X POST http://127.0.0.1:7200/reply --data-urlencode "inputtext=こんにちは" -H "Content-Type: application/x-www-form-urlencoded"

```


## 音声合成・対話の検証環境（streamlit環境）について
APIサーバーに加えてstreamlitアプリを立ち上げることで、ローカルで音声合成や音声対話を試すことが出来ます。

```
make streamlit
```

streamlitアプリを上記のコマンドで立ち上げた後、ブラウザで`http://localhost:8501`にアクセスしてください。
ログイン情報は、`./streamlit/auth.yml` のusernameとパスワードを参照してください。


## ディレクトリ構成

```
├── README.md
├── poetry.lock
├── pyproject.toml
├── pytest.ini
├── PDF  # マニフェストデータ
│   ├── ...
│   └── 東京都知事選挙2024マニフェストデック.pdf
├── Text
│   └── ...
├── faiss_knowledge
├── faiss_knowledge_manifest_demo_csv_db
├── faiss_qa
├── faiss_qa_db
├── qa_datasets
├── log
│   └── ... # 対話ログ(csv, json)
├── src
│   └── ... # ソースコード
└── tests
    └── ... # テストコード
```

## 利用パッケージのライセンスについて
音声合成に利用している `azure-cognitiveservices-speech` をダウンロードした時点で、Microsoft社のライセンスに同意したものとみなされます。
詳細は[PyPI](https://pypi.org/project/azure-cognitiveservices-speech/)上のLicence informationを参照してください。
