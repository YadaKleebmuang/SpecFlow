"""Action/template coverage; intent recognition is verified separately in phase 3."""

import importlib
import json
from pathlib import Path
import sqlite3
import sys
import unittest
from unittest.mock import Mock, patch

from linebot.models import FlexSendMessage
from rasa_sdk.executor import CollectingDispatcher

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEMPLATES = ROOT / 'app/rasa/actions/templates'

FAQ_FILES = {
    'ask_cpu_info': 'card_faq_cpu.json',
    'ask_gpu_info': 'card_faq_gpu.json',
    'ask_ram_info': 'card_faq_ram.json',
    'ask_ssd_hdd_diff': 'card_faq_ssd_hdd.json',
    'ask_mainboard_info': 'card_faq_mainboard.json',
    'ask_storage_info': 'card_faq_storage.json',
    'ask_psu_info': 'card_faq_psu.json',
    'ask_case_info': 'card_faq_case.json',
    'ask_cooler_info': 'card_faq_cooler.json',
    'ask_bot_capabilities': 'card_bot_capabilities.json',
}


def texts(node):
    if isinstance(node, list):
        return [text for child in node for text in texts(child)]
    if isinstance(node, dict):
        if node.get('type') == 'text':
            return [node['text']]
        return [text for value in node.values() for text in texts(value)]
    return []


class FAQActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Import-time init_db must not touch the user's analytics database.
        connect = sqlite3.connect
        with patch('sqlite3.connect', side_effect=lambda *args, **kwargs: connect(':memory:')):
            cls.actions = importlib.import_module('app.rasa.actions.actions')

    def run_faq(self, intent, channel='line', index=0):
        tracker = Mock()
        tracker.latest_message = {'intent': {'name': intent}}
        tracker.get_latest_input_channel.return_value = channel
        dispatcher = CollectingDispatcher()
        with patch.object(self.actions.random, 'randint', return_value=index):
            events = self.actions.ActionFAQ().run(dispatcher, tracker, {})
        self.assertEqual(events, [])  # An informational answer does not reset slots.
        self.assertEqual(len(dispatcher.messages), 1)
        return dispatcher.messages[0]

    def test_all_faq_intents_select_matching_line_variants(self):
        for intent, filename in FAQ_FILES.items():
            payload = json.loads((TEMPLATES / filename).read_text())
            cards = payload if isinstance(payload, list) else [payload]
            self.assertEqual(len(cards), 1 if intent == 'ask_bot_capabilities' else 3)
            for index, card in enumerate(cards):
                with self.subTest(intent=intent, variant=index):
                    message = self.run_faq(intent, index=index)
                    self.assertEqual(message['custom'], card)
                    self.assertIsNone(message['text'])

    def test_hardware_cli_text_matches_line_card_body(self):
        for intent, filename in FAQ_FILES.items():
            if intent == 'ask_bot_capabilities':
                continue
            cards = json.loads((TEMPLATES / filename).read_text())
            self.assertEqual(len({tuple(texts(card['contents']['body'])) for card in cards}), 3)
            for index, card in enumerate(cards):
                with self.subTest(intent=intent, variant=index):
                    message = self.run_faq(intent, 'rest', index)
                    self.assertEqual(message['text'], '\n'.join(texts(card['contents']['body'])))
                    self.assertFalse(message['custom'])

    def test_capabilities_text_describes_all_services_and_categories(self):
        message = self.run_faq('ask_bot_capabilities', 'rest')
        for phrase in ['จัดสเปค', 'อัปเกรด', 'คอขวด', 'ความรู้ฮาร์ดแวร์', 'คอมช้า',
                       'เล่นเกม', 'กราฟิก', 'ตัดต่อวิดีโอ', 'เขียนโปรแกรม', 'สำนักงาน',
                       'Mainboard', 'Storage', 'PSU', 'Case', 'Cooler']:
            self.assertIn(phrase, message['text'])

    def test_capabilities_buttons_send_the_planned_entry_messages(self):
        message = self.run_faq('ask_bot_capabilities')
        buttons = message['custom']['contents']['footer']['contents']
        self.assertEqual([button['action']['text'] for button in buttons], [
            'อยากจัดสเปคคอม', 'อยากอัปเกรดคอม', 'CPU คืออะไร', 'คอมช้าทำอย่างไร',
        ])
        for button in buttons:
            self.assertEqual(button['action']['type'], 'message')
            self.assertTrue(0 < len(button['action']['label']) <= 20)

    def test_hardware_cards_footer_has_single_start_build_button(self):
        for intent, filename in FAQ_FILES.items():
            if intent == 'ask_bot_capabilities':
                continue
            cards = json.loads((TEMPLATES / filename).read_text())
            for card in cards:
                buttons = card['contents']['footer']['contents']
                self.assertEqual(len(buttons), 1)
                button = buttons[0]
                self.assertEqual(button['action']['type'], 'message')
                self.assertEqual(button['action']['label'], 'เริ่มจัดสเปคคอม')
                self.assertEqual(button['action']['text'], 'อยากจัดสเปคคอม')
                self.assertEqual(button['style'], 'primary')
                self.assertEqual(button.get('color'), '#3498DB')

    def test_hardware_cards_have_quick_replies_excluding_self(self):
        topic_texts = {
            'ask_cpu_info': 'CPU คืออะไร',
            'ask_gpu_info': 'การ์ดจอคืออะไร',
            'ask_ram_info': 'RAM คืออะไร',
            'ask_ssd_hdd_diff': 'SSD ต่างกับ HDD ยังไง',
            'ask_mainboard_info': 'เมนบอร์ดคืออะไร',
            'ask_storage_info': 'Storage คืออะไร',
            'ask_psu_info': 'พาวเวอร์ซัพพลายคืออะไร',
            'ask_case_info': 'เคสคอมคืออะไร',
            'ask_cooler_info': 'ชุดระบายความร้อนคืออะไร',
        }
        for intent, filename in FAQ_FILES.items():
            if intent == 'ask_bot_capabilities':
                continue
            cards = json.loads((TEMPLATES / filename).read_text())
            for card in cards:
                self.assertIn('quickReply', card)
                items = card['quickReply']['items']
                self.assertEqual(len(items), 8)
                item_texts = [item['action']['text'] for item in items]
                for item in items:
                    self.assertEqual(item['type'], 'action')
                    self.assertEqual(item['action']['type'], 'message')
                    self.assertTrue(0 < len(item['action']['label']) <= 20)
                self.assertNotIn(topic_texts[intent], item_texts)

    def test_card_load_errors_fall_back_to_selected_text(self):
        errors = [FileNotFoundError('missing test template'),
                  json.JSONDecodeError('invalid test template', '', 0)]
        for intent in FAQ_FILES:
            for index in range(1 if intent == 'ask_bot_capabilities' else 3):
                expected = self.run_faq(intent, 'rest', index)['text']
                for error in errors:
                    with self.subTest(intent=intent, variant=index, error=type(error).__name__):
                        with patch.object(self.actions, 'load_static_card', side_effect=error), patch('builtins.print'):
                            message = self.run_faq(intent, index=index)
                        self.assertEqual(message['text'], expected)
                        self.assertFalse(message['custom'])

    def test_flex_payloads_can_be_serialized_by_installed_line_sdk(self):
        for intent, filename in FAQ_FILES.items():
            payload = json.loads((TEMPLATES / filename).read_text())
            for card in payload if isinstance(payload, list) else [payload]:
                with self.subTest(intent=intent, alt=card['altText']):
                    self.assertEqual(card['type'], 'flex')
                    self.assertTrue(0 < len(card['altText']) <= 400)
                    self.assertEqual(card['contents']['type'], 'bubble')
                    # Same constructor / deserializer used in LineOutput.send_custom_json.
                    message = FlexSendMessage.new_from_json_dict(card)
                    serialized = json.loads(message.as_json_string())
                    self.assertEqual(serialized, card)
                    self.assertLess(len(json.dumps(card['contents'], ensure_ascii=False).encode()), 30000)

    def test_unknown_or_missing_intent_returns_helpful_text(self):
        for intent in ['unknown_intent', '']:
            message = self.run_faq(intent)
            self.assertIn('ยังไม่มีข้อมูล', message['text'])
            self.assertFalse(message['custom'])

    def test_non_line_channels_do_not_load_cards(self):
        for channel in ['rest', 'cmdline', None]:
            with patch.object(self.actions, 'load_static_card') as load:
                message = self.run_faq('ask_bot_capabilities', channel)
                load.assert_not_called()
            self.assertIn('4 ด้าน', message['text'])

    def test_greet_card_has_footer_buttons(self):
        payload = json.loads((TEMPLATES / 'card_greet.json').read_text())
        self.assertEqual(len(payload), 2)
        for card in payload:
            self.assertEqual(card['type'], 'flex')
            buttons = card['contents']['footer']['contents']
            self.assertEqual(len(buttons), 3)
            self.assertEqual([b['action']['text'] for b in buttons], [
                'อยากจัดสเปคคอม', 'อยากอัปเกรดคอม', 'บอททำอะไรได้บ้าง'
            ])
            for b in buttons:
                self.assertEqual(b['action']['type'], 'message')
                self.assertTrue(0 < len(b['action']['label']) <= 20)
            message = FlexSendMessage.new_from_json_dict(card)
            self.assertEqual(json.loads(message.as_json_string()), card)

    def test_action_greet_channel_dispatch(self):
        tracker = Mock()
        tracker.latest_message = {'intent': {'name': 'greet'}}
        
        # Test Line channel
        tracker.get_latest_input_channel.return_value = 'line'
        dispatcher = CollectingDispatcher()
        events = self.actions.ActionGreet().run(dispatcher, tracker, {})
        self.assertEqual(events, [])
        self.assertEqual(len(dispatcher.messages), 1)
        self.assertIsNotNone(dispatcher.messages[0]['custom'])
        self.assertIn('footer', dispatcher.messages[0]['custom']['contents'])

        # Test REST channel
        tracker.get_latest_input_channel.return_value = 'rest'
        dispatcher = CollectingDispatcher()
        events = self.actions.ActionGreet().run(dispatcher, tracker, {})
        self.assertEqual(events, [])
        self.assertEqual(len(dispatcher.messages), 1)
        self.assertFalse(dispatcher.messages[0]['custom'])
        self.assertIn('SpecFlow', dispatcher.messages[0]['text'])


if __name__ == '__main__':
    unittest.main()
