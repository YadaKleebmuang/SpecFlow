import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts'), str(ROOT/'app/rasa')]
from prepare_five_category_data import items, key, NEW_INTENTS
from app.services.nlp.preprocessing import preprocess_thai_text
from app.services.recommendation.usage import classify_usage
from rasa.shared.core.domain import Domain
from rasa.shared.core.trackers import DialogueStateTracker
from rasa.shared.core.events import ActiveLoop, SlotSet, UserUttered, ActionExecuted
from rasa.core.actions.action import ActionExtractSlots
from rasa.core.channels.channel import CollectingOutputChannel


class FiveCategoryNLUWiringTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.domain = Domain.load(str(ROOT/'app/rasa/domain.yml'))
        cls.rules = yaml.safe_load((ROOT/'app/rasa/data/rules.yml').read_text())['rules']
        cls.rows = items(ROOT/'app/rasa/data/nlu.yml')

    def tracker(self, form, slot, intent, text, entities=None):
        return DialogueStateTracker.from_events('test', [
            ActiveLoop(form), SlotSet('requested_slot', slot),
            ActionExecuted('action_listen'),
            UserUttered(text, {'name':intent,'confidence':1.0}, entities=entities or []),
        ], slots=self.domain.slots)

    async def test_faq_never_fills_form_slots_even_with_spurious_entities(self):
        faqs = [i for i in self.domain.intents if i.startswith('ask_')]
        for form, slots in [('build_pc_form',['budget','usage','future_upgrade']),
                            ('upgrade_pc_form',['usage','current_specs'])]:
            for slot in slots:
                for intent in faqs:
                    with self.subTest(form=form, slot=slot, intent=intent):
                        tracker = self.tracker(form,slot,intent,'PSU 500W คืออะไร',[
                            {'entity':'budget','value':'500'}, {'entity':'usage','value':'PSU'}])
                        events = await ActionExtractSlots(None).run(CollectingOutputChannel(),Mock(),tracker,self.domain)
                        self.assertEqual(events, [])
                        self.assertEqual(tracker.get_slot('requested_slot'),slot)

    async def test_real_slot_answers_still_fill(self):
        cases=[('build_pc_form','budget','inform_budget','35000','35000'),
               ('build_pc_form','usage','inform_usage','เขียนโปรแกรม','เขียนโปรแกรม'),
               ('upgrade_pc_form','current_specs','inform_current_specs','CPU Ryzen 5600 RAM 8GB','CPU Ryzen 5600 RAM 8GB'),
               ('build_pc_form','future_upgrade','affirm','ใช่',True),
               ('build_pc_form','future_upgrade','deny','ไม่',False)]
        for form,slot,intent,text,value in cases:
            with self.subTest(slot=slot,intent=intent):
                tracker=self.tracker(form,slot,intent,text)
                events=await ActionExtractSlots(None).run(CollectingOutputChannel(),Mock(),tracker,self.domain)
                self.assertIn((slot,value),[(event.key,event.value) for event in events if isinstance(event,SlotSet)])

    def test_every_faq_has_standalone_and_form_resume_rules(self):
        for intent in [i for i in self.domain.intents if i.startswith('ask_')]:
            for form in [None,'build_pc_form','upgrade_pc_form']:
                matches=[rule for rule in self.rules if rule.get('condition')==[{'active_loop':form}]
                         and rule['steps'][0].get('intent')==intent]
                self.assertEqual(len(matches),1,(intent,form))
                self.assertEqual(matches[0]['steps'][1],{'action':'action_faq'})
                if form:
                    self.assertEqual(matches[0]['steps'][2:],[{'action':form},{'active_loop':form}])

    def test_nlu_domain_and_new_example_counts(self):
        labels={i for i,_ in self.rows}
        self.assertEqual(len(labels),21)
        self.assertTrue(labels.issubset(set(self.domain.intents)))
        for intent in NEW_INTENTS:
            self.assertGreaterEqual(sum(i==intent for i,_ in self.rows),20)

    def test_no_normalized_duplicates_or_test_leakage(self):
        train={key(t) for _,t in self.rows}
        self.assertEqual(len(train),len(self.rows))
        for path in ['app/rasa/tests/five_categories_nlu.yml','app/rasa/tests/nlu_test.yml',
                     'docs/dataset-engineering/holdout/locked-holdout-v1.yml']:
            test={key(t) for _,t in items(ROOT/path)}
            self.assertFalse(train & test,path)

    def test_line_preprocessed_buttons_retain_usage_category(self):
        for text, expected in [('เล่นเกม','gaming'),('งานกราฟิก','graphic'),
                               ('ตัดต่อวิดีโอ','video_editing'),('เขียนโปรแกรม','programming'),
                               ('งานสำนักงาน','office')]:
            with self.subTest(text=text):
                self.assertEqual(classify_usage(preprocess_thai_text(text)),expected)


if __name__=='__main__':
    unittest.main()
