from __future__ import annotations
import os
import sys
from typing import Any, Dict, List, Text

from rasa.engine.graph import ExecutionContext
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.engine.storage.resource import Resource
from rasa.engine.storage.storage import ModelStorage
from rasa.nlu.tokenizers.tokenizer import Token, Tokenizer
from rasa.shared.nlu.training_data.message import Message
from pythainlp import word_tokenize

@DefaultV1Recipe.register(
    DefaultV1Recipe.ComponentType.MESSAGE_TOKENIZER, is_trainable=False
)
class ThaiTokenizer(Tokenizer):
    def __init__(self, config: Dict[Text, Any]) -> None:
        # กำหนดค่าคอนฟิกเริ่มต้นของ Rasa Tokenizer เพื่อป้องกัน KeyError
        default_config = {
            "intent_tokenization_flag": False,
            "intent_split_symbol": "_",
            "case_sensitive": True,
        }
        merged_config = {**default_config, **config}
        super().__init__(merged_config)
        self.case_sensitive = merged_config.get("case_sensitive", True)

    @classmethod
    def create(
        cls,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
    ) -> ThaiTokenizer:
        return cls(config)

    def tokenize(self, message: Message, attribute: Text) -> List[Token]:
        text = message.get(attribute)
        if not text:
            return []

        if not self.case_sensitive:
            text = text.lower()

        # ตัดคำภาษาไทยโดยใช้ PyThaiNLP (newmm engine) และไม่รวมช่องว่าง (whitespace)
        words = word_tokenize(text, engine="newmm", keep_whitespace=False)

        return self._convert_words_to_tokens(words, text)
