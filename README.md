# AITuber

## 前提条件
* git-lfsがインストールされていること
  * マニフェストデック([こちらのファイル等](https://github.com/takahiroanno2024/aituber/blob/dev/python_server/PDF/%E6%9D%B1%E4%BA%AC%E9%83%BD%E7%9F%A5%E4%BA%8B%E9%81%B8%E6%8C%992024%E3%83%9E%E3%83%8B%E3%83%95%E3%82%A7%E3%82%B9%E3%83%88%E3%83%87%E3%83%83%E3%82%AF.pdf))ファイルのDLに必要
  * repoをcloneする前にgit-lfsが導入されている場合はclone時に自動的でファイルがDLされる
    * clone後にgit-lfsを導入した場合は、`git lfs pull`を実行してファイルをDL可能

## バックエンド側の環境構築

[README.md](python_server/README.md) を参照し、環境を構築して下さい。


## PDFファイルからRAG自動作成（作成中）

* PDF画像化のためにpopplerをインストール

    * Windowsの場合、以下のリンクのReleaseからzipをダウンロード： https://github.com/oschwartz10612/poppler-windows
        * ダウンロードしたZIPファイルを解凍し、任意の場所に配置します（例：C:\poppler-0.68.0）。
        * 解凍したフォルダのパスをシステムのPATH環境変数に追加します。
        * Windowsの検索バーで「環境変数」と入力し、「システム環境変数の編集」を選択します。
        * 「システム環境変数」の中の「Path」を選択し、「編集」をクリックします。
        * 新しいエントリを追加し、Popplerのbinフォルダ（例：C:\poppler-0.68.0\Library\bin）のパスを入力します。
        * すべてのダイアログで「OK」をクリックして環境変数の設定を保存します。
    * Macの場合
        * brew install poppler

* import_pdf.pyで画像化して保存
    * 一応画像インポート時にUnity側で画像のTexture typeを自動的に「Sprites」に設定している（Assets/Editor/TextureImporterSettings.cs）。もし設定されていなければ、メニューの「Assets」>「Set Texture Type to Sprite」を選択して実行するとTextureImporterSettings.csにて指定したフォルダ内を一括変換できる。

* マルチモーダルを使えるLLMでPDFを添付して下記プロンプトを実行し、作成したCSVファイルをダウンロード。(現状手動)

プロンプト

```
添付した日本語のPDFファイルのスライドの各ページの内容を整理して、title, text, filenameのカラムをもつCSVファイルにしてください。titleはスライド上部のタイトルをいれてください。textはスライド内で説明されている内容を入れてください。filenameはslide_{i+1}.pngとしてください。
```

* ダウンロードしたCSVで知識DB作成。

[知識 DB の作成](python_server/README.md#知識-DB-作成)

* get_faiss_vector.pyにて作成したDBのフォルダを設定。

* SlideDiplayers.cs内で指定している画像フォルダを修正

## 配信手順

* 用意するもの
    * Unity (2022.3.29f1)
    * OBS (https://obsproject.com/ja/download)
    * YouTubeアカウント

* OBSの設定
    * ソース→ウィンドウキャプチャでUnityの画面を映す。
    * プレビュー画面内でウィンドウキャプチャしている画面を選択して赤枠を表示させる。
    * 赤枠をドラッグアンドドロップで拡大縮小。Altキーを押しながらドラッグアンドドロップで切り抜き範囲の調整。
        * Gameタブを映します。
        * アプリ画面下部は画面外にして映さない想定です。

* Unityの操作
    * 初めの場合は、Asset/Scenes/SampleScene.unityをクリック。配信のためのシーンを読みだす。
    * もしConsole画面にVRMモデルのインポートに関するエラーが出ていたら、Unityにパッケージをインストールする必要があります。(https://www.ay3s-room.com/entry/unity-vrm-import-export).Universal RPやUniVRMなど。
    * Unity上でプレイボタンをクリック。
        * GameタブにてアバターがidleモーションをしていればOK。

* YouTubeの配信を開始
    * OBSにて「配信の管理」→「新しい配信の作成」などをして配信を作成。
        * 「限定公開」になっているか必ず確認すること。「非公開」だとコメントを取得できない。
    * YouTube Studioの「コンテンツ」→「ライブ配信」から、該当する配信のサムネイルをクリック。
    * 右側にある「動画リンク」をクリック。
    * 配信中の動画のURLの末尾の文字列をコピー。
    * リポジトリ内の.envのYT_IDを上書きする。


* 発話用ローカルサーバーを起動

必要に応じて、 [README.md](python_server/README.md) を参照し、環境を構築して下さい。

```
cd python_server
make run
```

* サーバーのテスト

```
curl -X POST http://127.0.0.1:7200/reply -d "inputtext=こんにちは" -H "Content-Type: application/x-www-form-urlencoded"
```

生成された返答が返ってくればOK

* Unity側のテスト
    * テストの開始
        * 「Play」ボタン（右向き△マークのボタン）をクリック。
    * 質問入力
        * 質問入力欄にテキストを入れてEnterで送信すると、出力がコメントウィンドウに表示され、回答が発話内容ウィンドウに表示され、音声が再生される。ログにも出力されている。
    * YouTubeコメントから発話
        * YouTube側でコメントを打つ。
        * アプリ画面下部の「コメント取得開始」ボタンをクリック。
        * コメントから一つを選んでコメントウィンドウに表示され、回答が発話内容ウィンドウに表示され、音声が再生される。ログにも出力されている。前回取得時から最大で5個のコメントが取得される。
        * 回答終了後、新しいコメントが無い場合、自動的に既定のコメント（ユーザー名：名無し）がランダムに選ばれる。
        * 「コメント取得停止」ボタンをクリックすると、ボタンが赤色に変わる。回答中のコメントの音声再生が止まると、そこで回答を終了する。
    * カメラ切り替え
        * カメラ位置を設定した位置に移動します。
    * ベンチマークテスト
        * 「ベンチマークテスト開始」ボタンをクリックすると、QueueManagerにて指定したCSVファイル内の質問を自動的にキューに追加して、全てに対して回答します。
        * 結果はlogフォルダに保存したcsvファイルを参照すると便利です。
    * Start/End ボタン
        * 配信開始・終了時の挨拶を登録しており、ボタンを押すと発話できる。

* stopwords  
一部、下記リンク先を参考にして作成
https://github.com/MosasoM/inappropriate-words-ja
