import importlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.recommendation.spec_recommender import SpecRecommender
from app.services.recommendation.upgrade_advisor import UpgradeAdvisor
from app.services.recommendation.usage import classify_usage


class FiveCategoryRecommendationTests(unittest.TestCase):
    usages = {
        "เล่นเกม": "gaming", "งานกราฟิก": "graphic", "ตัดต่อวิดีโอ": "video_editing",
        "เขียนโปรแกรม": "programming", "งานสำนักงาน": "office",
    }

    def test_classification_and_mixed_workloads(self):
        cases = dict(self.usages)
        cases.update({
            "เรียนเขียนโปรแกรม Python": "programming", "Docker VMs": "programming",
            "Blender 3D": "graphic", "Premiere": "video_editing", "Excel": "office",
            "เล่นเกมและเขียนโปรแกรม": "gaming", "เขียนโปรแกรมและเล่นเกม": "programming",
            "ตัดต่อวิดีโอและเรนเดอร์ 3D": "video_editing",
            "งานเอกสาร ใช้โปรแกรม Word": "office", "decode word": "office",
            "ไม่ระบุ": "gaming", "": "gaming",
        })
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(classify_usage(text), expected)

    def assert_complete_compatible(self, result, integrated, future):
        self.assertEqual(result['status'], 'success', result)
        parts = result['components']
        for name in ['cpu', 'motherboard', 'ram', 'storage', 'case', 'psu', 'cooler']:
            self.assertIsNotNone(parts[name], name)
        cpu, board = parts['cpu'], parts['motherboard']
        self.assertEqual(cpu['socket'], board['socket'])
        self.assertEqual(parts['ram']['type'], board['ram_type'])
        self.assertIn(board['form_factor'], parts['case']['form_factor_support'])
        self.assertIn(cpu['socket'], parts['cooler']['socket_support'])
        if integrated:
            self.assertIsNone(parts['gpu'])
            self.assertTrue(cpu['integrated_graphics'])
        else:
            self.assertIsNotNone(parts['gpu'])
        power = cpu['tdp'] + (parts['gpu']['power_draw'] if parts['gpu'] else 0) + 100
        self.assertGreaterEqual(parts['psu']['wattage'], power)
        if future:
            self.assertIn(cpu['socket'], ['AM5', 'LGA1700'])
            self.assertEqual(board['ram_type'], 'DDR5')

    def test_five_categories_budget_boundary_and_future_upgrade(self):
        recommender = SpecRecommender()
        for usage, category in self.usages.items():
            for budget, future in [(15000, False), (15999, False), (16000, False),
                                   (35000, False), (50000, True)]:
                with self.subTest(usage=usage, budget=budget, future=future):
                    result = recommender.get_recommendation(str(budget), usage, future)
                    self.assert_complete_compatible(result, budget < 16000, future)
                    self.assertEqual(result['usage_type'], category)
                    self.assertLessEqual(result['total_price'] * 100, budget * 110)
                    self.assertEqual(bool(result['warning']), result['total_price'] > budget)

    def test_allocations_change_selected_parts(self):
        recommender = SpecRecommender()
        # A common budget should favour GPU for games, CPU/RAM for programming.
        gaming = recommender.get_recommendation('50000', 'เล่นเกม')['components']
        programming = recommender.get_recommendation('50000', 'เขียนโปรแกรม')['components']
        self.assertGreater(gaming['gpu']['price'], programming['gpu']['price'])
        self.assertGreater(programming['cpu']['price'], gaming['cpu']['price'])
        self.assertGreaterEqual(programming['ram']['price'], gaming['ram']['price'])

    def test_over_budget_warning_and_rejection(self):
        recommender = SpecRecommender()
        result = recommender.get_recommendation('10000', 'งานสำนักงาน')
        self.assertEqual(result['status'], 'success')
        self.assertGreater(result['total_price'], 10000)
        self.assertIn(str(result['total_price'] - 10000), result['warning'])
        rejected = recommender.get_recommendation('10000', 'งานสำนักงาน', True)
        self.assertEqual(rejected['status'], 'error')
        self.assertIn('10%', rejected['text'])
        self.assertNotIn('components', rejected)

    def test_exact_ten_percent_budget_limit(self):
        recommender = SpecRecommender()
        # A single compatible AM4/iGPU build with no cheaper alternatives.
        prices = {'cpu': 3200, 'motherboard': 1800, 'ram': 1000, 'storage': 1000,
                  'case': 1000, 'psu': 2000, 'cooler': 1000}
        for category, price in prices.items():
            recommender.db[category] = [dict(recommender.db[category][0], price=price)]
        result = recommender.get_recommendation('10000', 'งานสำนักงาน')
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['total_price'], 11000)
        self.assertTrue(result['warning'])
        recommender.db['storage'][0]['price'] += 1
        self.assertEqual(recommender.get_recommendation('10000', 'งานสำนักงาน')['status'], 'error')

    def test_missing_required_components_never_succeeds(self):
        for category in ['cpu', 'motherboard', 'ram', 'gpu', 'storage', 'case', 'psu', 'cooler']:
            with self.subTest(category=category):
                recommender = SpecRecommender()
                recommender.db[category] = []
                self.assertEqual(recommender.get_recommendation('35000', 'เล่นเกม')['status'], 'error')
        recommender = SpecRecommender()
        recommender.db['gpu'] = []
        self.assertEqual(recommender.get_recommendation('15000', 'งานสำนักงาน')['status'], 'success')

    def test_incompatible_parts_are_rejected(self):
        for category, field, value in [('case', 'form_factor_support', []),
                                       ('cooler', 'socket_support', []), ('psu', 'wattage', 0)]:
            with self.subTest(category=category):
                recommender = SpecRecommender()
                for part in recommender.db[category]:
                    part[field] = value
                self.assertEqual(recommender.get_recommendation('35000', 'เล่นเกม')['status'], 'error')

    def test_programming_ram_advice(self):
        advisor = UpgradeAdvisor()
        for capacity in [2, 4, 8]:
            result = advisor.analyze_upgrade(f'Ryzen 5 5600 RAM {capacity}GB SSD 512GB', 'เขียนโปรแกรม')
            advice = ' '.join(result.get('recommendations', []))
            self.assertIn('16GB–32GB', advice)
            self.assertIn('Docker', advice)
            self.assertIn('DDR', advice)
            self.assertEqual(result['total_price'], 0)  # No guessed RAM type or price.

    def test_ram_detection_does_not_confuse_vram_or_larger_kits(self):
        advisor = UpgradeAdvisor()
        for ram in ['RAM 16GB', 'RAM 48GB', 'RAM 8GB x 2', 'RAM 2x8GB', 'VRAM 8GB',
                    'RAM 64GB GPU 4GB']:
            with self.subTest(ram=ram):
                result = advisor.analyze_upgrade(f'Ryzen 5 5600, {ram}, SSD 512GB', 'เขียนโปรแกรม')
                self.assertNotIn('**เพิ่ม RAM**', ' '.join(result.get('recommendations', [])))

    def test_ram_capacity_formats(self):
        for ram in ['RAM 8GB', 'แรม 8 กิ๊ก', 'RAM DDR4 8GB', '8GB RAM', 'RAM 2x4GB',
                    'RAM 4GB x 2', 'ram8']:
            with self.subTest(ram=ram):
                self.assertEqual(UpgradeAdvisor._ram_capacity(ram), 8)


class FiveCategoryActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.db_path = str(Path(cls.temp.name) / 'analytics.db')
        connect = sqlite3.connect
        # actions.py initializes SQLite at import; isolate this from user data.
        with patch('sqlite3.connect', side_effect=lambda *args, **kwargs: connect(cls.db_path)):
            cls.actions = importlib.import_module('app.rasa.actions.actions')
        cls.original_db_path = cls.actions.DB_PATH
        cls.actions.DB_PATH = cls.db_path

    @classmethod
    def tearDownClass(cls):
        cls.actions.DB_PATH = cls.original_db_path
        cls.temp.cleanup()

    def test_quick_replies_and_analytics_use_same_categories(self):
        payload = json.loads((ROOT / 'app/rasa/actions/templates/card_ask_usage.json').read_text())
        items = payload['quickReply']['items']
        self.assertEqual(len(items), 5)
        expected = ['เล่นเกม', 'กราฟิก', 'ตัดต่อวิดีโอ', 'เขียนโปรแกรม', 'ออฟฟิศ']
        for item, label in zip(items, expected):
            actual = self.actions.get_usage_type_db(item['action']['text'])
            self.assertEqual(actual, label)
            self.actions.log_search('test', actual, 35000, 34000)
        with sqlite3.connect(self.db_path) as connection:
            labels = {row[0] for row in connection.execute('SELECT usage_type FROM user_searches')}
        self.assertEqual(labels, set(expected))

    def test_line_and_cli_usage_prompt(self):
        from rasa_sdk.executor import CollectingDispatcher
        for channel in ['line', 'rest']:
            dispatcher = CollectingDispatcher()
            tracker = Mock()
            tracker.get_latest_input_channel.return_value = channel
            self.actions.ActionAskUsage().run(dispatcher, tracker, {})
            message = dispatcher.messages[0]
            if channel == 'line':
                self.assertEqual(len(message['custom']['quickReply']['items']), 5)
            else:
                for usage in FiveCategoryRecommendationTests.usages:
                    self.assertIn(usage, message['text'])

    def test_missing_line_template_falls_back_to_five_categories(self):
        from rasa_sdk.executor import CollectingDispatcher
        dispatcher = CollectingDispatcher()
        tracker = Mock()
        tracker.get_latest_input_channel.return_value = 'line'
        with patch.object(self.actions, 'load_static_card', side_effect=FileNotFoundError('test')):
            self.actions.ActionAskUsage().run(dispatcher, tracker, {})
        for usage in FiveCategoryRecommendationTests.usages:
            self.assertIn(usage, dispatcher.messages[0]['text'])

    def test_budget_warning_reaches_line_card(self):
        from rasa_sdk.executor import CollectingDispatcher
        dispatcher = CollectingDispatcher()
        tracker = Mock()
        tracker.get_latest_input_channel.return_value = 'line'
        tracker.get_slot.side_effect = {'budget': '10000', 'usage': 'งานสำนักงาน',
                                        'future_upgrade': False}.get
        with patch.object(self.actions, 'log_search'):
            self.actions.ActionRecommendPC().run(dispatcher, tracker, {})
        payload = json.dumps(dispatcher.messages[0]['custom'], ensure_ascii=False)
        self.assertIn('เกินงบ', payload)
        self.assertIn('เกินงบ 490 บาท', payload)


if __name__ == '__main__':
    unittest.main()
