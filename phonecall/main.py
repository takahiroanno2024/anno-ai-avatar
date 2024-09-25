# Standard library imports
import os
import sys

from dotenv import load_dotenv

# Third-party imports
from fastapi import FastAPI
from loguru import logger
from pyngrok import ngrok

from vocode.logging import configure_pretty_logging
from vocode.streaming.models.agent import ChatGPTAgentConfig, FillerAudioConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.telephony import TwilioConfig
from vocode.streaming.models.synthesizer import AzureSynthesizerConfig
from vocode.streaming.telephony.config_manager.redis_config_manager import RedisConfigManager
from vocode.streaming.telephony.server.base import TelephonyServer, TwilioInboundCallConfig
from vocode.streaming.models.transcriber import (
    DeepgramTranscriberConfig,
    PunctuationEndpointingConfig,
)

from custom_chatgpt_agent import CustomChatGPTAgentConfig, CustomChatGPTAgentFactory
from vocode.streaming.telephony.constants import DEFAULT_AUDIO_ENCODING, DEFAULT_SAMPLING_RATE


INITIAL_MESSAGE = "こんにちは！！お電話いただきありがとうございます！！私は東京都知事こうほの、あんの、たかひろ、の「AI」です！！本人の代わりに、私がみなさんのご意見やご質問をお聞きし、個人情報が残らない形で参考にさせていただきます！！何かご意見やご質問はありますか？"
PROMPT = """
あなたは市民と電話をしている選挙期間中の東京都知事候補です。質問を受けた場合は回答してください。質問がない場合は、普段の生活における困りごと・不満・要望を聞いてください。
一文は短く、回答は簡潔に分かりやすくお願いします。
# あなたの情報
* 名前: あんの たかひろ
* 一人称: 私
* 職業: SF作家、AIエンジニア
* 年齢: 33歳
* 性別: 男性
* 出身: 東京都
* 性格: 謙虚。敬意をもって答える。相手を気遣う。礼儀正しい。
* 口癖:
    * 「xxxをアップデート」
    * 相手に呼びかけるときは「私たち」と言う
# 注意点
* 道徳的・倫理的に適切な回答を心がけてください。
* 有権者の質問に対して、共感的な回答を心がけてください。特にテクノロジーに対して不安を持つ有権者に対しては、安心感を与えるような回答を心がけてください。
* 自分の政策を説明する際は、意気込みを伝えるようにしてください。
* この会話は東京都知事選挙で候補者の政策や情報、考えを説明するためのものです。都知事選挙や都政との関連性が低いと思われる話題（国政や外交など）には、「私はあんのが掲げる政策について学習しているので、それ以外の内容には答えられません。」のように回答してください。
    * 今回の東京知事選には、小池百合子氏、蓮舫氏、石丸伸二氏等が出馬しています。関連情報として彼らに関する情報が与えられている場合は、与えられている情報を参考にして、質問に回答しても問題ありません。
* もし関連情報に該当する知識がない場合は、回答を差し控えてください。
* 関連情報に基づき、なるべく具体的な政策を説明するようにしてください。
* 返答内容で、自身の性格については言及しないで下さい
* 想定する質問と回答の例を与えるので、もし質問内容と類似する想定回答が存在する場合は、その回答を参考に返答してください
* 絶対にMarkdownは使わないでください。絶対に箇条書きは使わない。話し言葉で分かりやすく語る。
* 攻撃的な質問を受けた場合は「すみません、その質問には答えられません。」と返してください。
* 複数の点について語るときは、「第一に〜。第二に〜。」というように、話し言葉で順序をつけて語る。
"""

FILLER_WORDS = ["なるほど！「------」「------」ありがとうございます！", "はい！ありがとうございます！「------」「------」お答えします！", "わかりました！「------」「------」お答えします！"]

RAG_URL = "http://host.docker.internal:7200"

# if running from python, this will load the local .env
# docker-compose will load the .env file by itself
load_dotenv()

configure_pretty_logging()

app = FastAPI(docs_url=None)

config_manager = RedisConfigManager()

BASE_URL = os.getenv("BASE_URL")

if not BASE_URL:
    ngrok_auth = os.environ.get("NGROK_AUTH_TOKEN")
    if ngrok_auth is not None:
        ngrok.set_auth_token(ngrok_auth)
    port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else 3000

    # Open a ngrok tunnel to the dev server
    BASE_URL = ngrok.connect(port).public_url.replace("https://", "")
    logger.info('ngrok tunnel "{}" -> "http://127.0.0.1:{}"'.format(BASE_URL, port))

if not BASE_URL:
    raise ValueError("BASE_URL must be set in environment if not using pyngrok")

telephony_server = TelephonyServer(
    base_url=BASE_URL,
    config_manager=config_manager,
    agent_factory=CustomChatGPTAgentFactory(),
    inbound_call_configs=[
        TwilioInboundCallConfig(
            url="/inboundcall",
            agent_config=CustomChatGPTAgentConfig(
                openai_api_key=os.environ.get("TOGETHER_API_KEY"),
                model_name="google/gemma-2-27b-it",
                max_tokens=1024,
                initial_message=BaseMessage(text=INITIAL_MESSAGE),
                prompt_preamble=PROMPT,
                filler_words=FILLER_WORDS,
                rag_url=RAG_URL
            ),
            twilio_config=TwilioConfig(
                account_sid=os.environ["TWILIO_ACCOUNT_SID"],
                auth_token=os.environ["TWILIO_AUTH_TOKEN"],
            ),
            transcriber_config=DeepgramTranscriberConfig.from_telephone_input_device(
                endpointing_config=PunctuationEndpointingConfig(),
                api_key=os.environ["DEEPGRAM_API_KEY"],
                # Change the language if trascription for a different language is needed
                language="ja",
                model="nova-2",
            ),
            synthesizer_config = AzureSynthesizerConfig.from_telephone_output_device(
                    voice_name="ja-JP-KeitaNeural",
                    language_code="ja-JP"
            ),
        )
    ],
)


app.include_router(telephony_server.get_router())
