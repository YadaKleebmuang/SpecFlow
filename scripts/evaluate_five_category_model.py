"""Record every prediction, including fallbacks, for raw and LINE input paths."""
import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from sklearn.metrics import accuracy_score, classification_report

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'app/rasa')]
from prepare_five_category_data import NEW_INTENTS, key
from app.services.nlp.preprocessing import preprocess_thai_text


def summarize(records):
    result = {}
    for mode in ['raw', 'line']:
        rows = [r for r in records if r['mode'] == mode]
        for scope in ['all', 'existing', 'new']:
            subset = [r for r in rows if scope == 'all' or (r['intent'] in NEW_INTENTS) == (scope == 'new')]
            labels = sorted({r['intent'] for r in subset})
            gold = [r['intent'] for r in subset]
            pred = [r['prediction'] for r in subset]
            report = classification_report(gold, pred, labels=labels, output_dict=True, zero_division=0)
            result[f'{mode}_{scope}'] = {'count': len(subset), 'accuracy': accuracy_score(gold, pred),
                'macro_f1': report['macro avg']['f1-score'], 'per_intent': report,
                'fallbacks': sum(r['prediction'] == 'nlu_fallback' for r in subset),
                'classifier_accuracy_without_fallback': accuracy_score(gold, [r['classifier_prediction'] for r in subset])}
        for entity in ['usage', 'budget']:
            relevant = [r for r in rows if any(e['entity'] == entity for e in r['gold_entities'])]
            tp = fp = fn = 0
            for row in rows:
                gold = {key(str(e['value'])) for e in row['gold_entities'] if e['entity'] == entity}
                pred = {key(str(e['value'])) for e in row['entities'] if e['entity'] == entity}
                tp += len(gold & pred); fp += len(pred-gold); fn += len(gold-pred)
            precision = tp/(tp+fp) if tp+fp else 0
            recall = tp/(tp+fn) if tp+fn else 0
            result[f'{mode}_{entity}_entity'] = {'examples_with_gold':len(relevant), 'tp':tp,'fp':fp,'fn':fn,
                'precision':precision,'recall':recall,'f1':2*precision*recall/(precision+recall) if precision+recall else 0,
                'unit':'normalized entity type/value match (not token-level)'}
    return result


async def evaluate(args):
    from rasa.core.agent import Agent
    from rasa.shared.nlu.training_data.loading import load_data
    examples = load_data(args.data).intent_examples
    agent = Agent.load(args.model)
    records = []
    for example in examples:
        text = example.get('text')
        for mode, query in [('raw', text), ('line', preprocess_thai_text(text))]:
            parsed = await agent.parse_message(query)
            ranking = [p for p in parsed.get('intent_ranking', []) if p['name'] != 'nlu_fallback']
            records.append({'id': hashlib.sha256((example.get('intent')+'::'+text).encode()).hexdigest(),
                'text':text, 'query':query,'intent':example.get('intent'), 'mode':mode,
                'prediction':parsed['intent']['name'],'confidence':parsed['intent']['confidence'],
                'classifier_prediction':ranking[0]['name'] if ranking else parsed['intent']['name'],
                'gold_entities':example.get('entities', []), 'entities':parsed.get('entities', [])})
    output = {'model':args.model, 'model_sha256':hashlib.sha256(Path(args.model).read_bytes()).hexdigest(),
              'data':args.data,'data_sha256':hashlib.sha256(Path(args.data).read_bytes()).hexdigest(),
              'metrics':summarize(records),'predictions':records}
    Path(args.out).write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:{m:v for m,v in value.items() if m != 'per_intent'} for k,value in output['metrics'].items()},indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model',required=True)
    parser.add_argument('--data',required=True)
    parser.add_argument('--out',required=True)
    asyncio.run(evaluate(parser.parse_args()))
