import json, os, sys
from datetime import datetime, timezone
import requests

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

COLLECTED_DIR = os.path.join(os.path.dirname(__file__), 'collected')
DATA_DIR = os.path.join(BASE, 'data')
os.makedirs(COLLECTED_DIR, exist_ok=True)

SES = requests.Session()
SES.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
})

def graphql(query):
    r = SES.post('https://api.tarkov.dev/graphql',
                 json={'query': query}, timeout=15)
    return r.json().get('data', {})

def fetch_current_ammo():
    data = graphql('{ ammo(item:{maxResults:300}) { id item { name shortName } caliber penPower damage fragChance } }')
    return data.get('ammo', [])

def fetch_current_tasks():
    data = graphql('{ tasks { id name taskType minPlayerLevel finishesRequired gameMode } }')
    return data.get('tasks', [])

def fetch_current_status():
    data = graphql('{ status { raidEndTimestamp messages { content type solveTime } } }')
    return data.get('status', {})

def load_snapshot():
    path = os.path.join(COLLECTED_DIR, 'snapshot.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def save_snapshot(data):
    path = os.path.join(COLLECTED_DIR, 'snapshot.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def detect_changes(current, snapshot_key, compare_fn):
    old = load_snapshot().get(snapshot_key, [])
    new_items = []
    for item in current:
        if not any(compare_fn(item, o) for o in old):
            new_items.append(item)
    return new_items

def main():
    now = datetime.now(timezone.utc)
    date_str = now.strftime('%Y-%m-%d')
    ts = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    old_snapshot = load_snapshot()

    results = {
        'timestamp': ts,
        'date': date_str,
        'new_ammo': [],
        'new_tasks': [],
        'status_messages': [],
    }

    print(f'[{date_str}] Checking Tarkov.dev API for updates...')

    print('  fetching ammo...')
    current_ammo = fetch_current_ammo()
    if old_snapshot.get('ammo'):
        old_ids = {a['id'] for a in old_snapshot['ammo']}
        new_ammo = [a for a in current_ammo if a['id'] not in old_ids]
        if new_ammo:
            print(f'  -> {len(new_ammo)} new ammo types found!')
            results['new_ammo'] = new_ammo
    else:
        print('  -> (first run, establishing baseline)')

    print('  fetching tasks...')
    current_tasks = fetch_current_tasks()
    if old_snapshot.get('tasks'):
        old_ids = {t['id'] for t in old_snapshot['tasks']}
        new_tasks = [t for t in current_tasks if t['id'] not in old_ids]
        if new_tasks:
            print(f'  -> {len(new_tasks)} new tasks found!')
            results['new_tasks'] = new_tasks
    else:
        print('  -> (first run, establishing baseline)')

    print('  fetching status...')
    status = fetch_current_status()
    if status.get('messages'):
        old_msgs = old_snapshot.get('status_messages', [])
        new_msgs = [m for m in status['messages'] if m not in old_msgs]
        if new_msgs:
            print(f'  -> {len(new_msgs)} new status messages!')
            results['status_messages'] = new_msgs

    save_snapshot({
        'ammo': current_ammo,
        'tasks': current_tasks,
        'status_messages': status.get('messages', []),
        'last_checked': ts,
    })

    path = os.path.join(COLLECTED_DIR, f'{date_str}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'  saved: {path}')

    return results


if __name__ == '__main__':
    result = main()
    has_new = result['new_ammo'] or result['new_tasks'] or result['status_messages']
    if has_new:
        print(f'\nNew content found!')
        print(f'  ammo: {len(result["new_ammo"])}')
        print(f'  tasks: {len(result["new_tasks"])}')
        print(f'  status msgs: {len(result["status_messages"])}')
    else:
        print('\nNo new content detected.')

    print('\nTo generate articles from this data, run: python3 tools/content_writer.py')
