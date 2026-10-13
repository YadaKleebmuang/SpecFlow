"""Train/evaluate candidate artifacts sequentially; never switches the live model."""
import hashlib
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/five-categories'
RASA = ROOT / '.venv-rasa-deploy/bin/rasa'
PYTHON = ROOT / '.venv-rasa-deploy/bin/python'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    env = {**os.environ, 'RASA_TELEMETRY_ENABLED':'false', 'PYTHONHASHSEED':'42',
           'PYTHONDONTWRITEBYTECODE':'1', 'PYTHONPATH':str(ROOT/'app/rasa'),
           'KERAS_HOME':'/tmp/.keras'}
    manifest = {'status':'running', 'stages':[], 'source_hashes':{str(p):hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
        for p in ['app/rasa/data/nlu.yml','app/rasa/config.yml','app/rasa/domain.yml','app/rasa/data/rules.yml',
                  'app/rasa/tests/five_categories_nlu.yml']}}
    manifest_path = BASE/'training-manifest.json'
    if args.resume:
        previous = json.loads(manifest_path.read_text())
        assert previous['source_hashes'] == manifest['source_hashes'], 'Cannot resume after source changes'
        manifest = previous
        manifest['status'] = 'running'
    def save():
        manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    def run(name, command, log):
        for path, sha in manifest['source_hashes'].items():
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == sha, f'Source changed: {path}'
        if args.resume and any(stage['name'] == name and stage.get('exit_code') == 0 for stage in manifest['stages']):
            print('Reusing completed stage:', name, flush=True)
            return
        stage={'name':name,'command':[str(x) for x in command],'start':time.time()}
        manifest['stages'].append(stage); save()
        print(name,flush=True)
        with open(log,'w') as output:
            code=subprocess.call(command,cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT)
        stage.update(exit_code=code,seconds=time.time()-stage['start']); save()
        if code:
            manifest['status']='failed'; save()
            raise SystemExit(f'{name} failed ({code}); see {log}')
    save()
    run('validate',[RASA,'data','validate','--config','app/rasa/config.yml','--domain','app/rasa/domain.yml',
                    '--data','app/rasa/data','--max-history','5'],BASE/'validation.log')
    for fold in range(5):
        folder=BASE/f'cv/fold-{fold}'
        model_dir=ROOT/f'models/five-categories/cv/fold-{fold}'
        model=model_dir/f'fold-{fold}.tar.gz'
        # The original run's first fold was trained interactively. Reuse it only
        # on explicit resume and only if its evaluated artifact still matches.
        reuse_zero = False
        evaluation = folder/'evaluation.json'
        if args.resume and fold == 0 and model.exists() and evaluation.exists():
            evidence = json.loads(evaluation.read_text())
            reuse_zero = evidence['model_sha256'] == hashlib.sha256(model.read_bytes()).hexdigest()
            assert reuse_zero, 'Fold 0 model changed since evaluation'
        if not reuse_zero:
            run(f'train-fold-{fold}',[RASA,'train','nlu','--config','app/rasa/config.yml',
                '--nlu',folder/'train.yml','--out',model_dir,'--fixed-model-name',f'fold-{fold}'],folder/'training.log')
        run(f'evaluate-fold-{fold}',[PYTHON,'-B','scripts/evaluate_five_category_model.py',
            '--model',model,'--data',folder/'validation.yml','--out',folder/'evaluation.json'],folder/'evaluation.log')
    sys.path.insert(0,str(ROOT/'scripts'))
    from evaluate_five_category_model import summarize
    predictions=[]
    for fold in range(5):
        for row in json.loads((BASE/f'cv/fold-{fold}/evaluation.json').read_text())['predictions']:
            predictions.append({**row,'fold':fold})
    assert len(predictions)==2*len({r['id'] for r in predictions})
    metrics=summarize(predictions)
    passed=bool(metrics['raw_all']['accuracy'] >= .9125 and metrics['raw_all']['macro_f1'] >= .9136)
    (BASE/'cv/summary.json').write_text(json.dumps({'metrics':metrics,'development_gate_passed':passed,
        'predictions':predictions},ensure_ascii=False,indent=2)+'\n')
    run('train-candidate',[RASA,'train','--config','app/rasa/config.yml','--domain','app/rasa/domain.yml',
        '--data','app/rasa/data/nlu.yml','app/rasa/data/rules.yml','app/rasa/data/stories.yml',
        '--out','models/five-categories/candidate','--fixed-model-name','candidate'],BASE/'candidate-training.log')
    model=ROOT/'models/five-categories/candidate/candidate.tar.gz'
    manifest['candidate_sha256']=hashlib.sha256(model.read_bytes()).hexdigest()
    manifest['development_gate_passed']=bool(passed)
    # Freeze test outcomes until development gates pass. No holdout-driven tuning.
    if passed:
        run('evaluate-new-test',[PYTHON,'-B','scripts/evaluate_five_category_model.py','--model',model,
            '--data','app/rasa/tests/five_categories_nlu.yml','--out',BASE/'new-test-evaluation.json'],BASE/'new-test-evaluation.log')
    manifest['status']='complete'; save()
    print('Completed; development gate:',passed,flush=True)


if __name__=='__main__':
    main()
