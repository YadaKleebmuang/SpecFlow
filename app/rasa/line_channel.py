import inspect
import json
import logging
import os
import sys
from typing import Text, Callable, Awaitable, Any, Dict, List, Optional

# บังคับเพิ่มพาธหลักของโครงการใน sys.path เพื่อให้สามารถเรียกโมดูล app ได้อย่างถูกต้อง
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse

from rasa.core.channels.channel import InputChannel, UserMessage, OutputChannel

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage

logger = logging.getLogger(__name__)

class LineOutput(OutputChannel):
    @classmethod
    def name(cls) -> Text:
        return "line"

    def __init__(self, line_bot_api: LineBotApi):
        self.line_bot_api = line_bot_api

    async def send_text_message(self, recipient_id: Text, text: Text, **kwargs: Any) -> None:
        message = TextSendMessage(text=text)
        try:
            self.line_bot_api.push_message(recipient_id, message)
        except Exception as e:
            logger.error(f"Failed to push text message to LINE: {e}")

    async def send_custom_json(self, recipient_id: Text, json_message: Dict[Text, Any], **kwargs: Any) -> None:
        try:
            if json_message.get("type") == "flex":
                alt_text = json_message.get("altText", "This is a Flex Message")
                message = FlexSendMessage(alt_text=alt_text, contents=json_message.get("contents"))
                self.line_bot_api.push_message(recipient_id, message)
            else:
                logger.warning(f"Unsupported custom message type: {json_message.get('type')}")
        except Exception as e:
            logger.error(f"Failed to push custom JSON message to LINE: {e}")

class LineInput(InputChannel):
    @classmethod
    def name(cls) -> Text:
        return "line"

    @classmethod
    def from_credentials(cls, credentials: Dict[Text, Any]) -> "LineInput":
        if not credentials:
            cls.raise_missing_credentials_exception()

        return cls(
            credentials.get("channel_secret"),
            credentials.get("channel_access_token")
        )

    def __init__(self, channel_secret: Text, channel_access_token: Text):
        self.channel_secret = channel_secret
        self.channel_access_token = channel_access_token
        self.line_bot_api = LineBotApi(channel_access_token)
        self.parser = WebhookParser(channel_secret)

    def blueprint(self, on_new_message: Callable[[UserMessage], Awaitable[None]]) -> Blueprint:
        custom_webhook = Blueprint(
            "custom_webhook_{}".format(type(self).__name__),
            inspect.getmodule(self).__name__,
        )

        @custom_webhook.route("/", methods=["GET"])
        async def health(request: Request) -> HTTPResponse:
            return response.json({"status": "ok"})

        @custom_webhook.route("/webhook", methods=["POST"])
        async def webhook(request: Request) -> HTTPResponse:
            signature = request.headers.get("X-Line-Signature")
            body = request.body.decode("utf-8")

            try:
                events = self.parser.parse(body, signature)
            except InvalidSignatureError:
                logger.error("Invalid LINE signature.")
                return response.text("Invalid signature", status=400)

            from app.services.nlp.preprocessing import preprocess_thai_text

            for event in events:
                if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
                    sender_id = event.source.user_id
                    text = event.message.text
                    # ดำเนินการตัดคำและทำความสะอาดคำภาษาไทยเบื้องต้นก่อนเข้าสู่สมองบอท Rasa NLU
                    preprocessed_text = preprocess_thai_text(text)
                    logger.info(f"LINE Input - Original: '{text}' | Preprocessed: '{preprocessed_text}'")
                    out_channel = LineOutput(self.line_bot_api)
                    user_msg = UserMessage(preprocessed_text, out_channel, sender_id, input_channel=self.name())
                    await on_new_message(user_msg)

            return response.text("OK")

        return custom_webhook
