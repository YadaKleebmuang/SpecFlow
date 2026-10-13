"""Offline Core + real SDK actions; no LINE API calls or user analytics writes."""
import asyncio
import importlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'app/rasa'),str(ROOT/'scripts')]
from rasa.core.agent import Agent
from rasa.core.channels.channel import CollectingOutputChannel, UserMessage
from rasa.utils.endpoints import EndpointConfig
from rasa_sdk.executor import ActionExecutor
from app.services.nlp.preprocessing import preprocess_thai_text
from app.services.recommendation.usage import classify_usage


class LocalActions(EndpointConfig):
    def __init__(self, executor):
        super().__init__(url='http://offline-actions.invalid/webhook')
        self.executor=executor

    async def request(self, **kwargs):
        return await self.executor.run(kwargs['json'])


class LineCollector(CollectingOutputChannel):
    @classmethod
    def name(cls):
        return 'line'


async def main():
    with tempfile.TemporaryDirectory() as folder:
        connection=sqlite3.connect
        db=str(Path(folder)/'analytics.db')
        with patch('sqlite3.connect', side_effect=lambda *args,**kwargs:connection(db)):
            actions=importlib.import_module('app.rasa.actions.actions')
        actions.DB_PATH=db
        executor=ActionExecutor(); executor.register_package(actions)
        model=ROOT/'models/five-categories/candidate/candidate.tar.gz'
        agent=Agent.load(str(model),action_endpoint=LocalActions(executor))
        results=[]
        async def send(sender,text,intent=None,entities=None,mode='raw'):
            query=preprocess_thai_text(text) if mode=='line' else text
            parse=None if intent is None else {'text':query,'intent':{'name':intent,'confidence':1.0},
                'intent_ranking':[{'name':intent,'confidence':1.0}],'entities':entities or []}
            output=LineCollector() if mode=='line' else CollectingOutputChannel()
            await agent.handle_message(UserMessage(query,output,sender,parse_data=parse,input_channel='line' if mode=='line' else 'rest'))
            tracker=await agent.tracker_store.retrieve(sender)
            return tracker, output.messages
        # NLU smoke probes are development/button checks, not independent test accuracy.
        probes=[('บอททำอะไรได้บ้าง','ask_bot_capabilities'),('เมนบอร์ดคืออะไร','ask_mainboard_info'),
                ('storage คืออะไร','ask_storage_info'),('PSU คืออะไร','ask_psu_info'),
                ('เคสคอมคืออะไร','ask_case_info'),('CPU cooler คืออะไร','ask_cooler_info'),
                ('อยากจัดสเปคคอม','build_pc'),('อยากอัปเกรดคอม','upgrade_pc'),
                ('CPU คืออะไร','ask_cpu_info'),('คอมช้าทำอย่างไร','optimize_performance')]
        usages=['เล่นเกม','งานกราฟิก','ตัดต่อวิดีโอ','เขียนโปรแกรม','งานสำนักงาน']
        probes += [(text,'inform_usage') for text in usages]
        for mode in ['raw','line']:
            for text,intent in probes:
                parsed=await agent.parse_message(preprocess_thai_text(text) if mode=='line' else text)
                results.append({'kind':'nlu_smoke','mode':mode,'text':text,'expected':intent,
                    'actual':parsed['intent']['name'],'passed':parsed['intent']['name']==intent})
        # Verify each FAQ can interrupt and resume every requested slot, with Core
        # predictions active and known intents injected to isolate dialogue behavior.
        faq=[intent for intent in agent.domain.intents if intent.startswith('ask_')]
        for form,slots in [('build_pc_form',['budget','usage','future_upgrade']),('upgrade_pc_form',['usage','current_specs'])]:
            for slot in slots:
                for intent in faq:
                    sender=f'{form}-{slot}-{intent}'
                    entities=[]
                    if form=='build_pc_form' and slot!='budget': entities.append({'entity':'budget','value':'35000'})
                    if slot in ['future_upgrade','current_specs']: entities.append({'entity':'usage','value':'เขียนโปรแกรม'})
                    start='build_pc' if form=='build_pc_form' else 'upgrade_pc'
                    before,_=await send(sender,'เริ่มจัดสเปค',start,entities)
                    before_slot=before.get_slot('requested_slot')
                    after,messages=await send(sender,'คำถามฮาร์ดแวร์',intent,[{'entity':'budget','value':'500'},{'entity':'usage','value':'PSU'}])
                    action_names=[e.action_name for e in after.events if hasattr(e,'action_name')]
                    results.append({'kind':'form_interruption','form':form,'slot':slot,'intent':intent,
                        'before_requested':before_slot,'after_requested':after.get_slot('requested_slot'),
                        'passed':before_slot==slot and after.get_slot('requested_slot')==slot and
                        after.active_loop_name==form and 'action_faq' in action_names and len(messages)>=2})
        for mode in ['raw','line']:
            for usage in usages:
                sender=f'flow-{mode}-{usage}'
                transcript=[]
                for text in ['อยากจัดสเปคคอม','35000',usage,'ไม่']:
                    tracker,messages=await send(sender,text,mode=mode)
                    transcript.append({'input':text,'messages':messages,'requested_slot':tracker.get_slot('requested_slot'),
                        'usage':tracker.get_slot('usage'),'intent':tracker.latest_message.intent.get('name')})
                all_actions=[e.action_name for e in tracker.events if hasattr(e,'action_name')]
                chosen=transcript[2]['usage']
                results.append({'kind':'build_flow','mode':mode,'usage':usage,'transcript':transcript,
                    'passed':'action_recommend_pc' in all_actions and chosen is not None and
                    classify_usage(chosen)==classify_usage(usage) and tracker.active_loop_name is None})
        report={'scope':'offline NLU/Core/SDK actions; no live LINE API', 'cases':len(results),
            'passed':sum(r['passed'] for r in results),'results':results}
        (ROOT/'docs/five-categories/runtime-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print('Runtime checks:',report['passed'],'/',report['cases'])
        for result in results:
            if not result['passed']: print({k:v for k,v in result.items() if k!='transcript'})
        return report['passed']==report['cases']


if __name__=='__main__':
    raise SystemExit(0 if asyncio.run(main()) else 1)
