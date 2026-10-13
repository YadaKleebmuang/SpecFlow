"""Build candidate data from the preserved baseline; never read test labels to train."""
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.services.nlp.preprocessing import preprocess_thai_text

EVIDENCE = ROOT / 'docs/five-categories'
NEW_INTENTS = ['ask_bot_capabilities', 'ask_mainboard_info', 'ask_storage_info',
               'ask_psu_info', 'ask_case_info', 'ask_cooler_info']


def items(path):
    data = yaml.safe_load(Path(path).read_text())
    result = []
    for entry in data['nlu']:
        if 'intent' not in entry:
            continue
        if 'text' in entry:
            result.append((entry['intent'], entry['text']))
        else:
            result.extend((entry['intent'], line.strip()[2:])
                          for line in entry['examples'].splitlines() if line.strip().startswith('- '))
    return result


def plain(text):
    return re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)


def key(text):
    return re.sub(r'[^\w]', '', preprocess_thai_text(plain(text)).lower())


class Dumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def represent_string(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|' if '\n' in data else None)


Dumper.add_representer(str, represent_string)


def write_nlu(path, rows):
    grouped = defaultdict(list)
    for intent, text in rows:
        grouped[intent].append(text)
    data = {'version': '3.1', 'nlu': [
        {'intent': intent, 'examples': '\n'.join('- ' + text for text in examples) + '\n'}
        for intent, examples in grouped.items()
    ]}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(yaml.dump(data, Dumper=Dumper, allow_unicode=True, sort_keys=False, width=120))


def write_folds(rows):
    from sklearn.model_selection import StratifiedKFold
    manifest = {'seed': 42, 'rows': len(rows), 'folds': []}
    splitter = StratifiedKFold(5, shuffle=True, random_state=42)
    for fold, (train_indices, validation_indices) in enumerate(splitter.split(rows, [i for i, _ in rows])):
        folder = EVIDENCE / f'cv/fold-{fold}'
        train = [rows[i] for i in train_indices]
        validation = [rows[i] for i in validation_indices]
        assert not {key(t) for _, t in train} & {key(t) for _, t in validation}
        write_nlu(folder / 'train.yml', train)
        write_nlu(folder / 'validation.yml', validation)
        manifest['folds'].append({
            'fold': fold, 'train': len(train), 'validation': len(validation),
            'validation_ids': [hashlib.sha256((i+'::'+plain(t)).encode()).hexdigest() for i, t in validation],
            'train_sha256': hashlib.sha256((folder/'train.yml').read_bytes()).hexdigest(),
            'validation_sha256': hashlib.sha256((folder/'validation.yml').read_bytes()).hexdigest(),
            'normalized_overlap': 0,
        })
    (EVIDENCE/'cv/split-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


def main():
    changes = []
    rows = []
    for intent, text in items(EVIDENCE / 'baseline/nlu.yml'):
        original = intent
        if re.search(r'\s+-\s+', text):
            changes.append({'action': 'remove_concatenated_example', 'intent': intent, 'text': text})
            continue
        if text.startswith('auto_generated_'):
            changes.append({'action': 'remove_auto_generated', 'intent': intent, 'text': text})
            continue
        p = plain(text).lower()
        if intent == 'deny' and any(k in p for k in ['เน้น ประหยัด พอ', 'เอา แบบ ธรรมดา พอ', 'ไม่อยากเปลี่ยนแปลง', 'ไม่ต้องการอัปเกรด', 'อยากได้แบบอื่น', 'ไม่ต้องเพิ่ม', 'ไม่ต้อง เผื่อ', 'ไม่ จำเป็น', 'ขอแบบอื่นดีกว่า']):
            changes.append({'action': 'remove_noisy_deny', 'intent': intent, 'text': text})
            continue
        if intent == 'ask_ssd_hdd_diff':
            if any(k in p for k in ['แพง กว่า', 'ไฟล์ งาน ขนาดใหญ่']):
                pass
            elif not (('ssd' in p or 'เอสเอสดี' in p) and ('hdd' in p or 'ฮาร์ดดิสก์' in p)):
                intent = 'ask_storage_info'
        elif intent == 'ask_storage_info':
            if (('ssd' in p or 'เอสเอสดี' in p) and ('hdd' in p or 'ฮาร์ดดิสก์' in p)):
                intent = 'ask_ssd_hdd_diff'
        elif intent == 'greet':
            if any(k in p for k in ['สนใจคอม', 'สร้างคอม', 'ซื้อคอม', 'ประกอบคอม']):
                intent = 'build_pc'
            elif any(k in p for k in ['อัปเกรดคอม', 'อัพเกรดคอม']):
                intent = 'upgrade_pc'
            elif 'ช่วย' in p and 'อะไร' in p:
                intent = 'ask_bot_capabilities'
            elif p in ['เริ่มต้น ใช้งาน', 'เริ่มต้นใช้งาน']:
                intent = 'inform_usage'
        elif intent == 'goodbye':
            if 'สวัสดี' in p:
                intent = 'greet'
        elif intent == 'affirm':
            if p == 'เผื่อ':
                intent = 'inform_future_upgrade'
            elif p in ['ยินดีครับ', 'ยินดี']:
                intent = 'greet'
            elif 'ขอบคุณ' in p:
                intent = 'goodbye'
            elif p in ['เอา', 'พร้อม']:
                changes.append({'action': 'remove_ambiguous_affirm', 'intent': intent, 'text': text})
                continue
        elif intent == 'inform_budget':
            if any(k in p for k in ['สำหรับคอม', 'อยากได้คอม', 'อยากทำคอม', 'อยากประกอบ', 'ต้องการคอม', 'แต่ต้องการ', 'อยากได้ดีสุด', 'จ่ายได้สูงสุด', 'ฉันมีงบประมาณสูงสุด', 'จ่ายได้ประมาณ']):
                intent = 'build_pc'
            elif any(k in p for k in ['อัปเกรด', 'อัพเกรด', 'เพิ่มงบ']):
                intent = 'upgrade_pc'
        elif intent == 'inform_usage':
            if any(k in p for k in ['ต้องการคอมสำหรับ', 'คอมจะใช้สำหรับ', 'คอมทำงานเป็น']):
                intent = 'build_pc'
        elif intent == 'upgrade_pc':
            if 'เพิ่มประสิทธิภาพเกม fps' in p:
                intent = 'optimize_performance'
        elif intent == 'inform_future_upgrade':
            if any(k in p for k in ['จะอัปเกรด', 'อยากอัปเกรด', 'มีแผนจะ', 'มีแผนอัปเกรด', 'วางแผนอัปเกรด', 'ตั้งใจจะเปลี่ยน', 'คิดจะอัปเกรด', 'คิดจะเปลี่ยน', 'ปีหน้า', 'ถ้ามีงบประมาณเพิ่ม', 'ในปีหน้า', 'อยากเพิ่ม', 'ต้องการอัปเกรด', 'มีแผนเพิ่ม', 'จะทำการอัปเกรด', 'คิดจะเพิ่ม', 'มีแนวคิดอัปเกรด']):
                intent = 'upgrade_pc'
            elif any(k in p for k in ['อยากได้คอม', 'สำหรับคอม']):
                intent = 'build_pc'
            elif p in ['ใช้ นานๆ', 'ใช้นานๆ']:
                intent = 'inform_usage'
        if intent != original:
            changes.append({'action': 'relabel', 'from': original, 'to': intent, 'text': text})
        rows.append((intent, text))
    for intent, text in items(EVIDENCE / 'data/additions.yml'):
        original = intent
        p = plain(text).lower()
        if intent == 'ask_storage_info' and (('ssd' in p or 'เอสเอสดี' in p) and ('hdd' in p or 'ฮาร์ดดิสก์' in p)):
            intent = 'ask_ssd_hdd_diff'
        elif intent == 'affirm' and p == 'เผื่อ':
            intent = 'inform_future_upgrade'
        if intent != original:
            changes.append({'action': 'relabel', 'from': original, 'to': intent, 'text': text})
        rows.append((intent, text))
    unique = {}
    for intent, text in rows:
        normalized = key(text)
        if normalized in unique:
            previous = unique[normalized]
            if previous[0] != intent:
                raise ValueError(f'Conflicting labels: {previous} vs {(intent, text)}')
            # Prefer annotated examples over plain duplicates.
            if text.count('](') > previous[1].count(']('):
                unique[normalized] = (intent, text)
                removed = previous[1]
            else:
                removed = text
            changes.append({'action': 'remove_normalized_duplicate', 'intent': intent, 'text': removed})
        else:
            unique[normalized] = (intent, text)
    # Text-only overlap check; frozen test labels never affect training labels.
    frozen_paths = [ROOT / 'app/rasa/tests/nlu_test.yml',
                    ROOT / 'docs/dataset-engineering/holdout/locked-holdout-v1.yml',
                    ROOT / 'app/rasa/tests/five_categories_nlu.yml']
    forbidden = {key(text) for path in frozen_paths for _, text in items(path)}
    rows = []
    for normalized, row in unique.items():
        if normalized in forbidden:
            changes.append({'action': 'exclude_frozen_test_overlap', 'intent': row[0], 'text': row[1]})
        else:
            rows.append(row)
    write_nlu(ROOT / 'app/rasa/data/nlu.yml', rows)
    write_folds(rows)
    manifest = {'seed': 42, 'counts': dict(Counter(intent for intent, _ in rows)),
                'rows': len(rows), 'changes': changes,
                'source_sha256': hashlib.sha256((EVIDENCE / 'baseline/nlu.yml').read_bytes()).hexdigest(),
                'candidate_sha256': hashlib.sha256((ROOT / 'app/rasa/data/nlu.yml').read_bytes()).hexdigest()}
    (EVIDENCE / 'data-preparation.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:v for k,v in manifest.items() if k != 'changes'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
