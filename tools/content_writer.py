import json, os, sys, re
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'data')
COLLECTED_DIR = os.path.join(os.path.dirname(__file__), 'collected')
ARTICLES_PATH = os.path.join(DATA_DIR, 'articles.json')

def load_articles():
    with open(ARTICLES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_articles(data):
    data['lastUpdated'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    with open(ARTICLES_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def slugify(text):
    s = text.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s[:60]

def article_exists(articles, title):
    return any(a['title'] == title for a in articles)

def next_id(articles, prefix='auto'):
    ids = [a['id'] for a in articles if a['id'].startswith(prefix)]
    nums = [int(a.replace(prefix, '').replace('-', '')) for a in ids
            if a.replace(prefix, '').replace('-', '').isdigit()]
    n = max(nums) + 1 if nums else 1
    return f'{prefix}-{n:03d}'

def gen_news_daily(data):
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    new_articles = []

    msg = data.get('status_messages', [])
    if msg:
        for m in msg:
            content = m.get('content', '').strip()
            if not content:
                continue
            title = f'BSG官方通知：{content[:60]}'
            if len(title) > 80:
                title = title[:77] + '...'
            new_articles.append({
                'id': next_id(load_articles(), 'bsg'),
                'title': title,
                'category': 'news',
                'categoryLabel': '新闻资讯',
                'icon': '📢',
                'views': 0,
                'comments': 0,
                'date': today,
                'timeAgo': '今天',
                'badge': 'new',
                'content': f'# BSG官方通知\n\n{content}\n\n> 数据来源：Escape from Tarkov 官方服务器状态',
                'summary': content[:120],
                'tags': ['BSG', '官方通知', '服务器状态'],
                'published': True,
            })

    new_ammo = data.get('new_ammo', [])
    for ammo in new_ammo:
        name = ammo.get('item', {}).get('name', ammo.get('id', ''))
        cal = ammo.get('caliber', '')
        title = f'新弹药数据变化：{name} ({cal})'
        pen = ammo.get('penPower', '?')
        dmg = ammo.get('damage', '?')
        new_articles.append({
            'id': next_id(load_articles(), 'ammo'),
            'title': title,
            'category': 'news',
            'categoryLabel': '新闻资讯',
            'icon': '🔫',
            'views': 0,
            'comments': 0,
            'date': today,
            'timeAgo': '今天',
            'badge': 'new',
            'content': f'# 弹药数据变化通知\n\n**弹药名称**：{name}\n**口径**：{cal}\n**穿透力**：{pen}\n**伤害**：{dmg}\n\n> 数据来源：Tarkov.dev API',
            'summary': f'{name} 的穿透力调整为 {pen}，伤害调整为 {dmg}',
            'tags': ['弹药数据', '版本更新'],
            'published': True,
        })

    new_tasks = data.get('new_tasks', [])
    for task in new_tasks:
        tname = task.get('name', task.get('id', ''))
        title = f'新任务加入：{tname}'
        new_articles.append({
            'id': next_id(load_articles(), 'task'),
            'title': title,
            'category': 'quest',
            'categoryLabel': '任务攻略',
            'icon': '📋',
            'views': 0,
            'comments': 0,
            'date': today,
            'timeAgo': '今天',
            'badge': 'new',
            'content': f'# 新任务通知\n\n**任务名称**：{tname}\n**最低等级要求**：{task.get("minPlayerLevel", "?")}\n**游戏模式**：{task.get("gameMode", "?")}\n\n> 数据来源：Tarkov.dev API',
            'summary': f'新任务 {tname} 已加入游戏',
            'tags': ['任务', '新内容'],
            'published': True,
        })

    return new_articles

def main():
    collected_files = sorted(os.listdir(COLLECTED_DIR),
                             key=lambda f: os.path.getmtime(os.path.join(COLLECTED_DIR, f)),
                             reverse=True)
    if not collected_files:
        print('No collected data found. Run content_collector.py first.')
        return

    latest = collected_files[0]
    if latest == 'snapshot.json':
        latest = collected_files[1] if len(collected_files) > 1 else None

    if not latest:
        print('No collected data files found.')
        return

    path = os.path.join(COLLECTED_DIR, latest)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    articles_data = load_articles()
    articles = articles_data['articles']

    new_articles = gen_news_daily(data)
    added = 0
    for a in new_articles:
        if not article_exists(articles, a['title']):
            articles.insert(0, a)
            added += 1

    if added == 0:
        print('No new articles to add.')
        return

    save_articles(articles_data)
    print(f'Added {added} new articles to articles.json')

    print('Regenerating articles...')
    os.chdir(BASE)
    os.system(f'{sys.executable} gen_static.py')
    print('Regenerating homepage...')
    os.system(f'{sys.executable} gen_static_data.py')

    print(f'\nDone! {added} new articles published.')
    for a in new_articles[:5]:
        print(f'  - {a["title"]}')


if __name__ == '__main__':
    main()
