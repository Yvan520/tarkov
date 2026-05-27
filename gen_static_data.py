#!/usr/bin/env python3
"""Generate static HTML pages for all data-driven pages (ammo, loadouts, quests, maps, articles listing)."""
import json, re, os, html, shutil

BASE = '/Users/admin/Documents/test/tarkov'
NEW_VER = 'v1.5.0'
OLD_VER = 'v1.4.0'

# ── Load JSON data ──
def load_json(path):
    with open(f'{BASE}/{path}', 'r', encoding='utf-8') as f:
        return json.load(f)

ammo_all = load_json('data/ammo.json')['ammo']
loadouts_all = load_json('data/loadouts.json')['loadouts']
quests_all = load_json('data/quests.json')['quests']
maps_all = load_json('data/maps.json')['maps']
articles_all = load_json('data/articles.json')['articles']

# ── Read article.html for layout ──
with open(f'{BASE}/article.html', 'r', encoding='utf-8') as f:
    article_html = f.read()

def extr(pat, txt):
    m = re.search(pat, txt, re.DOTALL)
    return m.group(1) if m else ''

nav_html = extr(r'(<nav class="nav">.*?</nav>)', article_html)
mobile_html = extr(r'(<div class="mobile-menu".*?</div>)', article_html)
search_html = extr(r'(<div class="search-ov".*?</div>)', article_html)
footer_html = extr(r'(<footer class="footer".*?</footer>)', article_html)

GA = '''<!-- Google Analytics placeholder -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-XXXXXXXXXX');
</script>'''
BD = '<meta name="baidu-site-verification" content="codeva-E78NFWmiO9" />'

# ├─ Shared JS (search, menu, etc.) ──
SHARED_JS = '''
function toggleMenu(){document.getElementById('mobileMenu').classList.toggle('open')}
function openSearch(){document.getElementById('searchOv').classList.add('on');setTimeout(()=>document.getElementById('smInput')?.focus(),100)}
function closeSearch(){document.getElementById('searchOv').classList.remove('on');document.getElementById('searchResults').style.display='none'}
function closeSearchOv(e){if(e.target===document.getElementById('searchOv'))closeSearch()}
document.addEventListener('keydown',function(e){if((e.ctrlKey||e.metaKey)&&e.key==='k'){e.preventDefault();openSearch()}if(e.key==='Escape')closeSearch()});
'''

def subdir_links(h):
    """Add ../ prefix to relative hrefs for subdirectory pages."""
    return re.sub(r'href="(?!http|#|/|\.\./)([^"]+)"', r'href="../\1"', h)

def version_bump(h):
    return h.replace(OLD_VER, NEW_VER)

# Prepare layout for subdirectory use
NAV_SD = version_bump(subdir_links(nav_html))
MOBILE_SD = version_bump(subdir_links(mobile_html))
SEARCH_SD = search_html
FOOTER_SD = version_bump(subdir_links(footer_html))

def get_page_css(page_html):
    m = re.search(r'<style>(.*?)</style>', page_html, re.DOTALL)
    return m.group(1) if m else ''

def get_hero(page_html):
    m = re.search(r'(<div class="page-hero".*?</div>)', page_html, re.DOTALL)
    return m.group(1) if m else ''

esc = html.escape

def build_page(title, desc, css, hero, main_content, extra_js='', search_data_js=''):
    full_js = search_data_js + '\n' + SHARED_JS + '\n' + extra_js
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{esc(desc)}">
<title>{esc(title)}</title>
{BD}
{GA}
<style>{css}</style>
</head>
<body>
{NAV_SD}
{MOBILE_SD}
{hero}
{main_content}
{SEARCH_SD}
{FOOTER_SD}
<script>
{full_js}
</script>
</body>
</html>'''


# ============================================================
# 1. AMMO page
# ============================================================
def build_ammo():
    src = open(f'{BASE}/ammo.html', encoding='utf-8').read()
    css = get_page_css(src)
    hero = get_hero(src)

    # Recommendation cards (same as hardcoded RECS)
    recs = [
        {'armor': '1-2级甲', 'name': 'RIP (.45 ACP)', 'pen': 22, 'price': '420₽'},
        {'armor': '3-4级甲', 'name': 'BP (7.62×39)', 'pen': 46, 'price': '380₽'},
        {'armor': '5级甲', 'name': '7N40 (5.45×39)', 'pen': 58, 'price': '960₽'},
        {'armor': '6级甲', 'name': 'M61 (7.62×51)', 'pen': 61, 'price': '3,200₽'},
    ]
    rec_html = '<div class="rec-grid">' + ''.join(
        f'<div class="rec-card"><div class="rec-armor">{r["armor"]}</div><div class="rec-name">{r["name"]}</div><div class="rec-pen">穿透：{r["pen"]}</div><div class="rec-price">{r["price"]}</div></div>'
        for r in recs
    ) + '</div>'

    # Calibers
    calibers = ['5.45×39', '5.56×45', '7.62×39', '7.62×51', '9×19', '.45 ACP']
    colors = ['#ff6644', '#44aaff', '#ffaa44', '#aa44ff', '#44ffaa', '#ff4488', '#ffcc44', '#44ccff', '#ff88aa', '#88ff44']

    # Sort ammo by penetration descending
    ammo_sorted = sorted(ammo_all, key=lambda a: a.get('penetration', 0), reverse=True)

    def armor_cells(ac_list):
        if not ac_list:
            return '<div class="armc-wrap"><span class="armc armc-n">-</span></div>'
        res = '<div class="armc-wrap">'
        for i, v in enumerate(ac_list):
            cls = 'armc-y' if v == 'yes' else ('armc-m' if v == 'maybe' else 'armc-n')
            res += f'<span class="armc {cls}">{i+1}</span>'
        return res + '</div>'

    rows = []
    for a in ammo_sorted:
        pen = a.get('penetration', 0)
        dmg = a.get('damage', 0)
        armd = a.get('armorDamage', 0)
        pct = min(100, round((pen / 70) * 100))
        pc = 'v-hi' if pen >= 50 else ('v-md' if pen >= 35 else 'v-lo')
        dc = 'v-hi' if dmg >= 70 else ('v-md' if dmg >= 50 else 'v-lo')
        c = a.get('color', '#666')
        price = a.get('price', '-')
        src_txt = a.get('source', '-')
        acs = armor_cells(a.get('armorClass', []))
        rows.append(f'''<tr>
<td><div class="td-name"><span class="cal-dot" style="background:{c}"></span>{a["name"]}</div></td>
<td><span style="font-size:10px;background:var(--bg2);border:1px solid var(--border);padding:2px 7px;border-radius:3px;color:var(--text2)">{a["caliber"]}</span></td>
<td><div class="pen-wrap"><div class="pen-track"><div class="pen-fill" style="width:{pct}%"></div></div><span class="{pc}">{pen}</span></div></td>
<td class="{dc}">{dmg}</td>
<td>{armd}%</td>
<td>{acs}</td>
<td style="color:var(--gold);font-family:var(--mono)">{price}</td>
<td style="font-size:11px;color:var(--text3)">{src_txt}</td>
</tr>''')

    cal_filter_btns = '<button class="f-btn on" onclick="filterCal(this, \'\')">全部口径</button>' + \
        ''.join(f'<button class="f-btn" onclick="filterCal(this, \'{c}\')">{c}</button>' for c in calibers)

    tbody = ''.join(rows)
    total = len(ammo_all)

    content_html = f'''<div class="wrap">
<div class="recommend-section">
<div class="rec-title">⚡ 各护甲等级推荐弹药</div>
{rec_html}
</div>
<div class="filter-section">
{cal_filter_btns}
<span class="sort-info">共 <b style="color:var(--gold)">{total}</b> 条数据 · 点击表头排序</span>
</div>
<div class="table-wrap">
<table>
<thead><tr>
<th class="sortable" onclick="doSort('name')">弹药名称</th>
<th>口径</th>
<th class="sort-desc" onclick="doSort('pen')">穿透力</th>
<th class="sortable" onclick="doSort('damage')">伤害</th>
<th class="sortable" onclick="doSort('armorDmg')">护甲伤害</th>
<th>可穿甲级</th>
<th class="sortable" onclick="doSort('priceNum')">参考价格</th>
<th>获取方式</th>
</tr></thead>
<tbody id="ammoTbody">{tbody}</tbody>
</table>
</div>
</div>'''

    _ammo_items = []
    for a in ammo_sorted:
        pn = a.get('priceNum')
        if pn is None and a.get('price'):
            try: pn = int(re.sub(r'[^\d]', '', a.get('price', '0')))
            except: pn = 0
        _ammo_items.append({
            'name': a['name'], 'caliber': a['caliber'],
            'pen': a.get('penetration', 0), 'damage': a.get('damage', 0),
            'armorDmg': a.get('armorDamage', 0),
            'priceNum': pn or 0,
            'price': a.get('price', '-'), 'source': a.get('source', '-'),
            'armorClass': a.get('armorClass', []), 'color': a.get('color', '#666')
        })

    js = f'''
const allAmmo = {json.dumps(_ammo_items, ensure_ascii=False)};
let calFilter='',sortKey='pen',sortDir=-1;

function render(){{
  let data=[...allAmmo];
  if(calFilter) data=data.filter(a=>a.caliber===calFilter);
  data.sort((a,b)=>{{
    const av=a[sortKey],bv=b[sortKey];
    if(typeof av==='string') return sortDir*av.localeCompare(bv,'zh');
    return sortDir*((av||0)-(bv||0));
  }});
  const colors=['#ff6644','#44aaff','#ffaa44','#aa44ff','#44ffaa','#ff4488','#ffcc44','#44ccff','#ff88aa','#88ff44'];
  document.getElementById('sortInfo').innerHTML='共 <b style="color:var(--gold)">'+data.length+'</b> 条数据 · 点击表头排序';
  document.getElementById('ammoTbody').innerHTML=data.length?data.map((a,i)=>{{
    const pct=Math.min(100,Math.round((a.pen/70)*100));
    const pc=a.pen>=50?'v-hi':a.pen>=35?'v-md':'v-lo';
    const dc=a.damage>=70?'v-hi':a.damage>=50?'v-md':'v-lo';
    const ac=a.armorClass||[];
    const acs='<div class="armc-wrap">'+[1,2,3,4,5,6].map(n=>{{const cls=n<=ac.length&&(ac[n-1]==='yes')?'armc-y':n<=ac.length&&(ac[n-1]==='maybe')?'armc-m':'armc-n';return '<span class="armc '+cls+'">'+n+'</span>';}}).join('')+'</div>';
    const pr=a.price||'-';
    return '<tr><td><div class="td-name"><span class="cal-dot" style="background:'+(a.color||colors[i%colors.length])+'"></span>'+a.name+'</div></td><td><span style="font-size:10px;background:var(--bg2);border:1px solid var(--border);padding:2px 7px;border-radius:3px;color:var(--text2)">'+a.caliber+'</span></td><td><div class="pen-wrap"><div class="pen-track"><div class="pen-fill" style="width:'+pct+'%"></div></div><span class="'+pc+'">'+a.pen+'</span></div></td><td class="'+dc+'">'+a.damage+'</td><td>'+a.armorDmg+'%</td><td>'+acs+'</td><td style="color:var(--gold);font-family:var(--mono)">'+pr+'</td><td style="font-size:11px;color:var(--text3)">'+(a.source||'-')+'</td></tr>';
  }}).join(''):'<tr><td colspan="8" style="text-align:center;padding:24px;color:var(--text3)">暂无该口径弹药数据</td></tr>';
}}
function filterCal(btn,cal){{calFilter=cal;document.querySelectorAll('.f-btn').forEach(b=>b.classList.remove('on'));btn.classList.add('on');render()}}
function doSort(key){{
  sortDir=sortKey===key?sortDir*-1:-1;sortKey=key;
  document.querySelectorAll('th').forEach(th=>{{th.classList.remove('sort-asc','sort-desc','sortable');const oc=th.getAttribute('onclick')||'';if(oc.includes(key))th.classList.add(sortDir===-1?'sort-desc':'sort-asc');else if(oc.includes('doSort'))th.classList.add('sortable')}});
  render();
}}
initSearch();render();
'''

    search_js = f'''
const searchData={json.dumps([{'title': a['name']+' ('+a['caliber']+')', 'icon': '💊', 'url': '../ammo/', 'cat': '弹药'} for a in ammo_all], ensure_ascii=False)};
function doSearch(kw){{
  kw=kw.trim().toLowerCase();
  const el=document.getElementById('searchResults');
  if(!kw){{el.style.display='none';return}}
  const results=searchData.filter(s=>s.title.toLowerCase().includes(kw)).slice(0,8);
  if(!results.length){{el.style.display='block';el.innerHTML='<div class="sr-empty">未找到相关内容</div>';return}}
  el.style.display='block';
  el.innerHTML=results.map(r=>'<a href="'+r.url+'" class="sr-item"><span class="sr-icon">'+r.icon+'</span><div class="sr-body"><div class="sr-title">'+r.title+'</div><span class="sr-cat">'+r.cat+'</span></div></a>').join('');
}}
initSearch=function(){{}};
'''

    return build_page('弹药数据 | 塔科夫攻略站', '逃离塔科夫弹药数据库，穿透力、伤害、护甲穿透完整数据', css, hero, content_html, js, search_js)


# ============================================================
# 2. LOADOUTS page
# ============================================================
def build_loadouts():
    src = open(f'{BASE}/loadouts.html', encoding='utf-8').read()
    css = get_page_css(src)
    hero = get_hero(src)

    type_labels = {'pvp': '🔴 PVP', 'pve': '🟢 PVE', 'all': '🔵 全能'}
    budget_labels = {'low': '低预算', 'mid': '中等预算', 'high': '高端配置'}

    cards = []
    for i, l in enumerate(loadouts_all):
        icon = l.get('icon', '🔫')
        name = l['name']
        price = l.get('price', '')
        recoil = l.get('recoil', '0')
        ergo = l.get('ergo', '0')
        weight = l.get('weight', '0')
        ammo = l.get('ammo', '')
        tips = l.get('tips', '')
        budget = l.get('budget', '')
        ltype = l.get('type', 'pvp')
        parts = l.get('parts', [])

        tags_html = f'<span class="lt lt-rec">推荐</span><span class="lt lt-pvp">{type_labels.get(ltype, ltype)}</span>'
        if budget:
            tags_html += f'<span class="lt lt-bgt">{budget_labels.get(budget, budget)}</span>'
        ammo_html = f'<div class="lc-ammo">💊 推荐弹药：<b style="color:var(--text1)">{ammo}</b></div>' if ammo else ''
        tips_html = f'<div style="font-size:11px;color:var(--text3);margin-top:6px">{tips}</div>' if tips else ''

        cards.append(f'''<div class="lc" onclick="showDetail({i})">
<div class="lc-header"><span class="lc-name">{icon} {name}</span><span class="lc-price">{price}</span></div>
<div class="lc-img">{icon}</div>
<div class="lc-stats">
<div class="ls"><span class="ls-v">{recoil}</span><span class="ls-l">后坐力</span></div>
<div class="ls"><span class="ls-v">{ergo}</span><span class="ls-l">人机</span></div>
<div class="ls"><span class="ls-v">{weight}kg</span><span class="ls-l">重量</span></div>
</div>
<div class="lc-body">
<div class="lc-tags">{tags_html}</div>
{ammo_html}
{tips_html}
</div>
</div>''')

    grid = ''.join(cards)

    # Detail modal content for each loadout
    detail_data = []
    for l in loadouts_all:
        parts = l.get('parts', [])
        parts_html = ''.join(f'<li>{p}</li>' for p in parts) if parts else ''
        detail_data.append({
            'icon': l.get('icon', '🔫'),
            'name': l['name'],
            'recoil': l.get('recoil', '0'),
            'ergo': l.get('ergo', '0'),
            'weight': l.get('weight', '0'),
            'price': l.get('price', ''),
            'ammo': l.get('ammo', ''),
            'tips': l.get('tips', ''),
            'parts_html': parts_html
        })

    content_html = f'''<div class="wrap">
<div class="filter-tabs">
<div class="f-tab on" onclick="switchBudget(this,'')">📋 全部配装</div>
<div class="f-tab" onclick="switchBudget(this,'low')">💚 低预算 <span class="bg bg-low">&lt;50K</span></div>
<div class="f-tab" onclick="switchBudget(this,'mid')">💛 中等 <span class="bg bg-mid">50-150K</span></div>
<div class="f-tab" onclick="switchBudget(this,'high')">👑 高端 <span class="bg bg-hi">&gt;150K</span></div>
<div class="f-tab" onclick="switchBudget(this,'pvp')">🎯 PVP专精</div>
<div class="f-tab" onclick="switchBudget(this,'pve')">🌿 PVE稳定</div>
</div>
<div class="loadouts-grid" id="loadoutsGrid">{grid}</div>
</div>
<div class="detail-overlay" id="detailOverlay" onclick="closeDetail(event)">
<div class="detail-modal" onclick="event.stopPropagation()">
<div class="dm-header"><span class="dm-title" id="dmTitle">配装详情</span><div class="dm-close" onclick="closeDetail()">✕</div></div>
<div class="dm-body" id="dmBody"></div>
</div>
</div>'''

    js = f'''
const allLoadouts = {json.dumps(loadouts_all, ensure_ascii=False)};
let budgetFilter='',selectedId=-1;

function render(){{
  let data=[...allLoadouts];
  if(budgetFilter==='pvp') data=data.filter(l=>l.type==='pvp');
  else if(budgetFilter==='pve') data=data.filter(l=>l.type==='pve');
  else if(budgetFilter) data=data.filter(l=>l.budget===budgetFilter);
  if(!data.length){{document.getElementById('loadoutsGrid').innerHTML='<div class="empty">暂无该分类配装方案</div>';return;}}
  const typeL={{'pvp':'🔴 PVP','pve':'🟢 PVE','all':'🔵 全能'}};
  const budgetL={{'low':'低预算','mid':'中等预算','high':'高端配置'}};
  document.getElementById('loadoutsGrid').innerHTML=data.map((l,i)=>'<div class="lc '+(selectedId===i?'selected':'')+'" onclick="showDetail('+i+')"><div class="lc-header"><span class="lc-name">'+(l.icon||'🔫')+' '+l.name+'</span><span class="lc-price">'+l.price+'</span></div><div class="lc-img">'+(l.icon||'🔫')+'</div><div class="lc-stats"><div class="ls"><span class="ls-v">'+l.recoil+'</span><span class="ls-l">后坐力</span></div><div class="ls"><span class="ls-v">'+l.ergo+'</span><span class="ls-l">人机</span></div><div class="ls"><span class="ls-v">'+l.weight+'kg</span><span class="ls-l">重量</span></div></div><div class="lc-body"><div class="lc-tags"><span class="lt lt-rec">推荐</span><span class="lt lt-pvp">'+(typeL[l.type]||l.type)+'</span>'+(l.budget==='low'?'<span class="lt lt-bgt">低预算</span>':l.budget==='mid'?'<span class="lt lt-bgt">中等预算</span>':l.budget==='high'?'<span class="lt lt-bgt">高端配置</span>':'')+'</div>'+(l.ammo?'<div class="lc-ammo">💊 推荐弹药：<b style="color:var(--text1)">'+l.ammo+'</b></div>':'')+(l.tips?'<div style="font-size:11px;color:var(--text3);margin-top:6px">'+l.tips+'</div>':'')+'</div></div>').join('');
}}
function showDetail(i){{
  let data=[...allLoadouts];
  if(budgetFilter==='pvp') data=data.filter(l=>l.type==='pvp');
  else if(budgetFilter==='pve') data=data.filter(l=>l.type==='pve');
  else if(budgetFilter) data=data.filter(l=>l.budget===budgetFilter);
  const l=data[i]; if(!l) return;
  selectedId=i;
  document.getElementById('dmTitle').textContent=(l.icon||'🔫')+' '+l.name;
  const parts=l.parts||[];
  document.getElementById('dmBody').innerHTML='<div class="dm-stats"><div class="dm-stat"><span class="dm-stat-v">'+l.recoil+'</span><span class="dm-stat-l">后坐力</span></div><div class="dm-stat"><span class="dm-stat-v">'+l.ergo+'</span><span class="dm-stat-l">人机精度</span></div><div class="dm-stat"><span class="dm-stat-v">'+l.weight+'kg</span><span class="dm-stat-l">总重量</span></div></div><div class="dm-section"><div class="dm-sec-title">💰 预算参考</div><div style="font-size:16px;font-weight:700;color:var(--gold);font-family:var(--mono)">'+l.price+'</div></div>'+(l.ammo?'<div class="dm-section"><div class="dm-sec-title">💊 推荐弹药</div><div style="font-size:14px;font-weight:600;color:var(--text1)">'+l.ammo+'</div></div>':'')+(parts.length?'<div class="dm-section"><div class="dm-sec-title">🔧 配件清单</div><ul class="dm-parts">'+parts.map(p=>'<li>'+p+'</li>').join('')+'</ul></div>':'')+(l.tips?'<div class="dm-section"><div class="dm-sec-title">💡 使用建议</div><div style="font-size:13px;color:var(--text2);line-height:1.7">'+l.tips+'</div></div>':'');
  document.getElementById('detailOverlay').classList.add('show');
}}
function closeDetail(e){{if(!e||e.target===document.getElementById('detailOverlay'))document.getElementById('detailOverlay').classList.remove('show');}}
function switchBudget(btn,b){{budgetFilter=b;document.querySelectorAll('.f-tab').forEach(t=>t.classList.remove('on'));btn.classList.add('on');render()}}
document.addEventListener('keydown',function(e){{if(e.key==='Escape')closeDetail()}});
initSearch();render();
'''

    search_js = f'''
const searchData={json.dumps([{'title': l['name'], 'icon': l.get('icon', '🔫'), 'url': '../loadouts/', 'cat': '配装'} for l in loadouts_all], ensure_ascii=False)};
function doSearch(kw){{
  kw=kw.trim().toLowerCase();
  const el=document.getElementById('searchResults');
  if(!kw){{el.style.display='none';return}}
  const results=searchData.filter(s=>s.title.toLowerCase().includes(kw)).slice(0,8);
  if(!results.length){{el.style.display='block';el.innerHTML='<div class="sr-empty">未找到相关内容</div>';return}}
  el.style.display='block';
  el.innerHTML=results.map(r=>'<a href="'+r.url+'" class="sr-item"><span class="sr-icon">'+r.icon+'</span><div class="sr-body"><div class="sr-title">'+r.title+'</div><span class="sr-cat">'+r.cat+'</span></div></a>').join('');
}}
initSearch=function(){{}};
'''

    return build_page('武器配装 | 塔科夫攻略站', '逃离塔科夫武器配装推荐，按预算分类的最优配装方案', css, hero, content_html, js, search_js)


# ============================================================
# 3. QUESTS page
# ============================================================
def build_quests():
    src = open(f'{BASE}/quests.html', encoding='utf-8').read()
    css = get_page_css(src)
    hero = get_hero(src)

    merchants_data = [
        {'name': '全部任务', 'icon': '📋', 'key': ''},
        {'name': '帕帕', 'icon': '🦔', 'key': '帕帕'},
        {'name': '机修工', 'icon': '🔧', 'key': '机修工'},
        {'name': '治疗者', 'icon': '🩺', 'key': '治疗者'},
        {'name': '和平卫士', 'icon': '🎖️', 'key': '和平卫士'},
        {'name': '铁路员', 'icon': '🚂', 'key': '铁路员'},
        {'name': '犹大', 'icon': '👨‍💼', 'key': '犹大'},
    ]

    diff_style_map = {
        '简单': 'background:rgba(74,140,92,.2);color:#6aaa7a',
        '中等': 'background:rgba(192,112,48,.2);color:#e09050',
        '困难': 'background:rgba(192,80,80,.2);color:#c05050',
        '极难': 'background:rgba(144,48,200,.2);color:#9060d0',
        'easy': 'background:rgba(74,140,92,.2);color:#6aaa7a',
        'medium': 'background:rgba(192,112,48,.2);color:#e09050',
        'hard': 'background:rgba(192,80,80,.2);color:#c05050',
        'extreme': 'background:rgba(144,48,200,.2);color:#9060d0',
    }

    # Merchant sidebar
    def count_for_merchant(key):
        if not key:
            return len(quests_all)
        return sum(1 for q in quests_all if (q.get('merchant') or '').find(key) >= 0)

    merchant_items = []
    for m in merchants_data:
        cnt = count_for_merchant(m['key'])
        on = 'on' if not m['key'] else ''
        merchant_items.append(
            f'<div class="merchant-item {on}" onclick="selectMerchant(\'{m["key"]}\', \'{m["name"]}\')">'
            f'<span class="merchant-icon">{m["icon"]}</span>'
            f'<span class="merchant-name">{m["name"]}</span>'
            f'<span class="merchant-count">{cnt}</span></div>'
        )

    merchant_html = ''.join(merchant_items)

    # Quest cards
    quest_cards = []
    for i, q in enumerate(quests_all):
        diff = q.get('diffLabel') or q.get('difficulty') or ''
        desc = q.get('description') or q.get('desc') or ''
        reward = q.get('itemReward') or q.get('rewardItem') or ''
        exp = q.get('exp', '')
        if exp:
            try:
                exp_str = str(int(re.sub(r'[^\d]', '', str(exp))))
            except:
                exp_str = str(exp)
        else:
            exp_str = ''
        rep = q.get('rep', '')
        guide = q.get('guide', '暂无详细攻略，欢迎在评论区分享你的经验！')
        merchant = q.get('merchant', '')
        mic = q.get('merchantIcon', '')

        ds = diff_style_map.get(diff, '')

        qc = f'''<div class="qc" id="qc{i}">
<div class="qc-hd" onclick="toggleQ({i})">
<div class="qc-left">
<div class="qc-name">{q["name"]}</div>
<div class="qc-desc">{desc}</div></div>
<div class="qc-right">
<span class="qc-diff" style="{ds}">{diff}</span>
<span>{mic} {merchant}</span></div>
<span class="qc-expand">›</span></div>
<div class="qc-body">
<div class="qc-rewards">
{('<span class="qr qr-exp">⭐ '+exp_str+' EXP</span>') if exp_str else ''}
{('<span class="qr qr-rep">📈 声誉 '+rep+'</span>') if rep else ''}
{('<span class="qr qr-item">🎁 '+reward+'</span>') if reward else ''}
</div>
<div class="qc-guide">{"<p>"+guide.replace(chr(10),"</p><p>")+"</p>"}</div>
</div></div>'''
        quest_cards.append(qc)

    quest_list_html = ''.join(quest_cards)

    content_html = f'''<div class="wrap">
<div class="merchants-sidebar">
<div class="sidebar-title">选择商人</div>
<div id="merchantList">{merchant_html}</div>
</div>
<div class="quests-main">
<div class="quests-header">
<h2 id="currentMerchantTitle">全部任务</h2>
<div class="diff-filter">
<button class="d-btn on" onclick="filterDiff(this,'')">全部</button>
<button class="d-btn" onclick="filterDiff(this,'简单')">🟢 简单</button>
<button class="d-btn" onclick="filterDiff(this,'中等')">🟡 中等</button>
<button class="d-btn" onclick="filterDiff(this,'困难')">🔴 困难</button>
<button class="d-btn" onclick="filterDiff(this,'极难')">💀 极难</button>
</div>
</div>
<div class="quest-list" id="questList">{quest_list_html}</div>
</div>
</div>'''

    js = f'''
const allQuests = {json.dumps(quests_all, ensure_ascii=False)};
const MERCHANTS = {json.dumps(merchants_data, ensure_ascii=False)};
const diffStyle = {json.dumps(diff_style_map, ensure_ascii=False)};
let merchantFilter='',diffFilter='';

function renderMerchants(){{
  document.getElementById('merchantList').innerHTML=MERCHANTS.map(m=>{{
    const count=m.key?allQuests.filter(q=>(q.merchant||'').includes(m.key)).length:allQuests.length;
    return '<div class="merchant-item '+(merchantFilter===m.key?'on':'')+'" onclick="selectMerchant(\\''+m.key+'\\',\\''+m.name+'\\')"><span class="merchant-icon">'+m.icon+'</span><span class="merchant-name">'+m.name+'</span><span class="merchant-count">'+count+'</span></div>';
  }}).join('');
}}
function selectMerchant(key,name){{merchantFilter=key;document.getElementById('currentMerchantTitle').textContent=name==='全部任务'?'全部任务':name+' 的任务';renderMerchants();renderQuests()}}

function renderQuests(){{
  let data=[...allQuests];
  if(merchantFilter) data=data.filter(q=>(q.merchant||'').includes(merchantFilter));
  if(diffFilter) data=data.filter(q=>q.difficulty===diffFilter||q.diffLabel===diffFilter);
  if(!data.length){{document.getElementById('questList').innerHTML='<div class="empty">暂无相关任务数据</div>';return;}}
  document.getElementById('questList').innerHTML=data.map((q,i)=>{{
    const diff=q.diffLabel||q.difficulty||'';
    const desc=q.description||q.desc||'';
    const reward=q.itemReward||q.rewardItem||'';
    const exp=q.exp?String(parseInt((q.exp+'').replace(/[^\\d]/g,''))||0):'';
    const rep=q.rep||'';
    const guide=q.guide||'暂无详细攻略';
    return '<div class="qc" id="qc'+i+'"><div class="qc-hd" onclick="toggleQ('+i+')"><div class="qc-left"><div class="qc-name">'+q.name+'</div><div class="qc-desc">'+desc+'</div></div><div class="qc-right"><span class="qc-diff" style="'+(diffStyle[diff]||'')+'">'+diff+'</span><span>'+(q.merchantIcon||'')+' '+(q.merchant||'')+'</span></div><span class="qc-expand">›</span></div><div class="qc-body"><div class="qc-rewards">'+(exp?'<span class="qr qr-exp">⭐ '+exp+' EXP</span>':'')+(rep?'<span class="qr qr-rep">📈 声誉 '+rep+'</span>':'')+(reward?'<span class="qr qr-item">🎁 '+reward+'</span>':'')+'</div><div class="qc-guide">'+guide.split(String.fromCharCode(10)).map(l=>l.trim()?'<p>'+l+'</p>':'').join('')+'</div></div></div>';
  }}).join('');
}}
function toggleQ(i){{var el=document.getElementById('qc'+i);el.classList.toggle('open')}}
function filterDiff(btn,d){{diffFilter=d;document.querySelectorAll('.d-btn').forEach(b=>b.classList.remove('on'));btn.classList.add('on');renderQuests()}}
initSearch();
'''

    search_js = f'''
const searchData={json.dumps([{'title': q['name'], 'icon': q.get('merchantIcon', '📋'), 'url': '../quests/', 'cat': '任务'} for q in quests_all], ensure_ascii=False)};
function doSearch(kw){{
  kw=kw.trim().toLowerCase();
  const el=document.getElementById('searchResults');
  if(!kw){{el.style.display='none';return}}
  const results=searchData.filter(s=>s.title.toLowerCase().includes(kw)).slice(0,8);
  if(!results.length){{el.style.display='block';el.innerHTML='<div class="sr-empty">未找到相关内容</div>';return}}
  el.style.display='block';
  el.innerHTML=results.map(r=>'<a href="'+r.url+'" class="sr-item"><span class="sr-icon">'+r.icon+'</span><div class="sr-body"><div class="sr-title">'+r.title+'</div><span class="sr-cat">'+r.cat+'</span></div></a>').join('');
}}
initSearch=function(){{}};
'''

    return build_page('任务攻略 | 塔科夫攻略站', '逃离塔科夫任务攻略大全，各商人任务详细说明和完成指南', css, hero, content_html, js, search_js)


# ============================================================
# 4. MAPS page
# ============================================================
def build_maps():
    src = open(f'{BASE}/maps.html', encoding='utf-8').read()
    css = get_page_css(src)
    hero = get_hero(src)

    # Map definitions with full detail (merged from source defaults and JSON)
    def_maps = [
        {'id': 'customs', 'name': '海关', 'nameEn': 'Customs', 'icon': '🏭', 'difficulty': '新手友好', 'time': 45, 'players': 12, 'exits': 7, 'boss': '獾', 'tags': ['新手推荐', '任务丰富', 'Boss·獾'], 'exits_list': ['南方出口', '工厂出口', '铁路出口', 'ZB-1011', 'ZB-1012', '老加油站', '共检站'], 'loot': ['三层宿舍（高价值）', '工厂区储物柜', '油罐区箱子', 'USEC营地'], 'tips': ['白天光线好适合新手', '三层宿舍竞争激烈', '獾Boss在停车场附近出现', '建议从南方出口撤离']},
        {'id': 'woods', 'name': '森林', 'nameEn': 'Woods', 'icon': '🌲', 'difficulty': '中等', 'time': 50, 'players': 14, 'exits': 5, 'boss': '沙皇', 'tags': ['远程狙击', 'Boss·沙皇', '任务要地'], 'exits_list': ['猎人小屋', '河边出口', '山顶出口', '旧锯木厂', 'RUAF路堤'], 'loot': ['锯木厂区域', '地堡入口', 'SCAV据点'], 'tips': ['开阔地带注意狙击手', '沙皇有多名手下', '任务物品多在林中小屋', '建议带狙击枪']},
        {'id': 'interchange', 'name': '互换', 'nameEn': 'Interchange', 'icon': '🏬', 'difficulty': '中等', 'time': 50, 'players': 14, 'exits': 4, 'boss': '克莱格', 'tags': ['高价值物资', 'Boss·克莱格', '近战激烈'], 'exits_list': ['电力站', '铁路停车场', 'OLI收货区', 'Kiba入口'], 'loot': ['ULTRA商场中心', 'OLI仓库', 'KIBA武器店', 'Techlight'], 'tips': ['关闭电力可激活出口', '克莱格在KIBA或OLI附近', '室内近战为主', '电子设备价值高']},
        {'id': 'reserve', 'name': '储备基地', 'nameEn': 'Reserve', 'icon': '🏰', 'difficulty': '困难', 'time': 55, 'players': 12, 'exits': 6, 'boss': '格鲁特', 'tags': ['军事物资', 'Boss·格鲁特', '撤离复杂'], 'exits_list': ['装甲列车（信号弹）', '地下停机坪', '白色主教', '黑色主教', 'D-2', 'V-Ex'], 'loot': ['地下军事仓库', '直升机停机坪', '武器库'], 'tips': ['装甲列车需信号弹激活', '格鲁特防御能力极强', '地下区域物资丰富', '撤离点分散需提前规划']},
        {'id': 'shoreline', 'name': '海岸线', 'nameEn': 'Shoreline', 'icon': '🌊', 'difficulty': '困难', 'time': 50, 'players': 12, 'exits': 8, 'boss': '桑塔', 'tags': ['医疗资源', 'Boss·桑塔', '地图超大'], 'exits_list': ['码头', '村庄北', '村庄南', '山坡出口', '路障出口', '温泉出口', '岩石通道', '破损围栏'], 'loot': ['度假村（顶级医疗）', '气象站', '雷达基地', '码头仓库'], 'tips': ['地图巨大建议规划路线', '桑塔在度假村内', '医疗物资价值极高', '需要钥匙解锁房间']},
        {'id': 'labs', 'name': '实验室', 'nameEn': 'The Lab', 'icon': '🔬', 'difficulty': '极难', 'time': 35, 'players': 10, 'exits': 3, 'boss': '狂人', 'tags': ['需要通行证', '顶级装备', 'Boss·狂人'], 'exits_list': ['飞机库（4个按钮）', '停车场', '技术出口'], 'loot': ['研究室（顶级物资）', '服务器房间', '医疗实验室'], 'tips': ['进入需要实验室通行证', '狂人是最危险的Boss', '出口需要多人配合激活', '全员顶配才敢进']},
        {'id': 'factory', 'name': '工厂', 'nameEn': 'Factory', 'icon': '🏭', 'difficulty': '中等', 'time': 25, 'players': 6, 'exits': 4, 'boss': '', 'tags': ['近战激烈', '节奏快', 'PVP热门'], 'exits_list': ['办公楼出口', '停车场', '门3出口', '沼泽地出口'], 'loot': ['工厂内部箱子', '保险箱室'], 'tips': ['地图小节奏极快', '近战武器优势明显', '适合练习枪法', '资源相对较少']},
        {'id': 'lighthouse', 'name': '灯塔', 'nameEn': 'Lighthouse', 'icon': '🗼', 'difficulty': '困难', 'time': 50, 'players': 12, 'exits': 5, 'boss': '教徒', 'tags': ['高价值', 'Boss·教徒', '任务要地'], 'exits_list': ['北岸出口', '旧停车场', '村庄出口', '山顶信标', '轮渡码头'], 'loot': ['豪华别墅区', '灯塔基地', '水处理厂'], 'tips': ['教徒AI极为精准', '别墅区物资丰富', '地图西侧危险区域', '建议高配才进']},
        {'id': 'darkcorner', 'name': '黑暗之角', 'nameEn': 'Dark Corner', 'icon': '🌑', 'difficulty': '困难', 'time': 45, 'players': 12, 'exits': 5, 'boss': '暗影', 'tags': ['新地图', '0.15新增', '高价值'], 'exits_list': ['北部仓库门', '地下通道（需钥匙）', '屋顶直升机（信号弹）', '东侧围栏', '南部停车场'], 'loot': ['银行金库', '医院顶层', '警察局', '地下室'], 'tips': ['新地图请仔细探索', '地下室物资丰富', '暗影Boss较难击杀', '建议组队进入']},
        {'id': 'center', 'name': '中心区', 'nameEn': 'Streets', 'icon': '🏙️', 'difficulty': '新手友好', 'time': 45, 'players': 10, 'exits': 6, 'boss': '科隆泰', 'tags': ['1-20级专属', 'Boss·科隆泰', 'BTR装甲车'], 'exits_list': ['Klimov街', '地下通道', '法院后方', '大厦停车场', '铁路桥', '购物中心出口'], 'loot': ['银行金库', '云霄大厦办公室', 'TerraGroup总部', '医院'], 'tips': ['1-20级新手专属', 'BTR装甲车提供安全移动', 'Boss科隆泰在购物中心附近', '推荐利用BTR出租车撤离']},
        {'id': 'groundzero', 'name': '航站楼', 'nameEn': 'Terminal', 'icon': '🏗️', 'difficulty': '困难', 'time': 45, 'players': 10, 'exits': 4, 'boss': '终局Boss', 'tags': ['新地图1.0', '高难度撤离', 'PVP密集'], 'exits_list': ['主航站楼出口', '紧急通道', '货运通道', '直升机撤离'], 'loot': ['航站楼大厅保险箱', '控制塔服务器房', '货运区高级武器箱', '地下通道隐藏物资'], 'tips': ['需要完成全部前置任务', '进入需要高配装备', '推荐组队进入', '辐射区域需要防辐射装备']},
    ]

    map_bg = {
        'customs': 'linear-gradient(135deg,#1a2a1a,#2a3a2a)', 'woods': 'linear-gradient(135deg,#1a2a15,#2a3a1a)',
        'interchange': 'linear-gradient(135deg,#1a1a2a,#252535)', 'reserve': 'linear-gradient(135deg,#252525,#352525)',
        'shoreline': 'linear-gradient(135deg,#15252a,#1a3040)', 'labs': 'linear-gradient(135deg,#0a1520,#102030)',
        'factory': 'linear-gradient(135deg,#1a1510,#2a2018)', 'lighthouse': 'linear-gradient(135deg,#101a20,#182535)',
        'darkcorner': 'linear-gradient(135deg,#0d0d1a,#1a0a2a)', 'center': 'linear-gradient(135deg,#1a2028,#253040)',
        'groundzero': 'linear-gradient(135deg,#1a1520,#2a2030)'
    }
    diff_class = {'新手友好': 'd-easy', 'easy': 'd-easy', '中等': 'd-mid', 'medium': 'd-mid', '困难': 'd-hard', 'hard': 'd-hard', '极难': 'd-ex', 'extreme': 'd-ex'}

    # Merge JSON data with defaults
    merged_maps = []
    for m_base in def_maps:
        json_match = [x for x in maps_all if x['id'] == m_base['id']]
        if json_match:
            merged = dict(m_base)
            merged.update(json_match[0])
            merged_maps.append(merged)
        else:
            merged_maps.append(m_base)

    # Build map cards HTML
    map_cards = []
    for i, m in enumerate(merged_maps):
        bg = map_bg.get(m['id'], 'linear-gradient(135deg,#1a2020,#202a2a)')
        dc = diff_class.get(m['difficulty'] or m.get('difficulty', ''), 'd-mid')
        tags = m.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',') if t.strip()]
        tags_html = ''.join(f'<span class="map-tag">{t}</span>' for t in tags)
        boss_html = f'<span>👹 {m["boss"]}</span>' if m.get('boss') else ''

        map_cards.append(f'''<div class="map-card" onclick='showDetail("{m["id"]}")'>
<div class="map-img" style="background:{bg}"><span>{m.get("icon","🗺️")}</span><span class="map-diff {dc}">{m.get("difficulty","")}</span></div>
<div class="map-body">
<div class="map-name">{m.get("name","")}<span class="map-name-en">{m.get("nameEn","")}</span></div>
<div class="map-meta"><span>⏱ {m.get("time",0)}分钟</span><span>👥 {m.get("players",0)}人</span><span>🚪 {m.get("exits",0)}个出口</span>{boss_html}</div>
<div class="map-tags">{tags_html}</div>
<span class="map-btn">查看详情 →</span>
</div>
</div>''')

    maps_grid = ''.join(map_cards)

    content_html = f'''<div class="wrap">
<div class="diff-tabs">
<button class="d-tab on" onclick="filterDiff(this,'')">全部</button>
<button class="d-tab" onclick="filterDiff(this,'新手友好')">🟢 新手友好</button>
<button class="d-tab" onclick="filterDiff(this,'中等')">🟡 中等难度</button>
<button class="d-tab" onclick="filterDiff(this,'困难')">🔴 困难</button>
<button class="d-tab" onclick="filterDiff(this,'极难')">💀 极难</button>
</div>
<div class="maps-grid" id="mapsGrid">{maps_grid}</div>
<div class="detail-panel" id="detailPanel"></div>
</div>'''

    js = f'''
const allMaps = {json.dumps(merged_maps, ensure_ascii=False)};
const mapBg = {json.dumps(map_bg, ensure_ascii=False)};
const diffClass = {json.dumps(diff_class, ensure_ascii=False)};
let diffFilter='',activeId='';

function renderMaps(){{
  let data=[...allMaps];
  if(diffFilter) data=data.filter(m=>m.difficulty===diffFilter||(m.difficulty||'').toLowerCase()===diffFilter.toLowerCase());
  if(!data.length){{document.getElementById('mapsGrid').innerHTML='<div class="empty">暂无符合条件的地图</div>';return;}}
  document.getElementById('mapsGrid').innerHTML=data.map(m=>{{
    const bg=mapBg[m.id]||'linear-gradient(135deg,#1a2020,#202a2a)';
    const dc=diffClass[m.difficulty]||'d-mid';
    const tags=Array.isArray(m.tags)?m.tags:(m.tags||'').split(',').map(t=>t.trim()).filter(Boolean);
    return '<div class="map-card '+(activeId===m.id?'active-card':'')+'" onclick="showDetail(\\''+m.id+'\\')"><div class="map-img" style="background:'+bg+'"><span>'+(m.icon||'🗺️')+'</span><span class="map-diff '+dc+'">'+m.difficulty+'</span></div><div class="map-body"><div class="map-name">'+m.name+'<span class="map-name-en">'+(m.nameEn||'')+'</span></div><div class="map-meta"><span>⏱ '+m.time+'分钟</span><span>👥 '+m.players+'人</span><span>🚪 '+m.exits+'个出口</span>'+(m.boss?'<span>👹 '+m.boss+'</span>':'')+'</div><div class="map-tags">'+tags.map(t=>'<span class="map-tag">'+t+'</span>').join('')+'</div><span class="map-btn">查看详情 →</span></div></div>';
  }}).join('');
}}
function showDetail(id){{
  const m=allMaps.find(x=>x.id===id); if(!m) return;
  activeId=m.id; renderMaps();
  const exits=m.exits_list||[]; const loot=m.loot||[]; const tips=m.tips||[];
  document.getElementById('detailPanel').innerHTML='<div class="detail-header"><div class="detail-icon">'+(m.icon||'🗺️')+'</div><div class="detail-title"><h2>'+m.name+' <span style="font-size:16px;color:var(--text3);font-weight:400">'+(m.nameEn||'')+'</span></h2><div class="sub">'+(m.desc||'')+'</div></div><div class="close-btn" onclick="closeDetail()">✕</div></div><div class="detail-stats"><div class="ds-item"><span class="ds-val">'+m.time+'</span><span class="ds-label">分钟时长</span></div><div class="ds-item"><span class="ds-val">'+m.players+'</span><span class="ds-label">最大玩家</span></div><div class="ds-item"><span class="ds-val">'+m.exits+'</span><span class="ds-label">出口数量</span></div><div class="ds-item"><span class="ds-val">'+(m.boss||'无')+'</span><span class="ds-label">Boss</span></div></div><div class="detail-sections">'+(exits.length?'<div class="ds-sec"><div class="ds-sec-title">🚪 出口列表</div><ul class="ds-list">'+exits.map(e=>'<li>'+e+'</li>').join('')+'</ul></div>':'')+(loot.length?'<div class="ds-sec"><div class="ds-sec-title">💰 主要物资点</div><ul class="ds-list">'+loot.map(e=>'<li>'+e+'</li>').join('')+'</ul></div>':'')+(tips.length?'<div class="ds-sec" style="grid-column:1/-1"><div class="ds-sec-title">💡 攻略要点</div><ul class="ds-list">'+tips.map(e=>'<li>'+e+'</li>').join('')+'</ul></div>':'')+'</div>';
  document.getElementById('detailPanel').classList.add('show');
  document.getElementById('detailPanel').scrollIntoView({{behavior:'smooth',block:'start'}});
}}
function closeDetail(){{activeId='';document.getElementById('detailPanel').classList.remove('show');renderMaps()}}
function filterDiff(btn,d){{diffFilter=d;document.querySelectorAll('.d-tab').forEach(b=>b.classList.remove('on'));btn.classList.add('on');closeDetail();renderMaps()}}
initSearch();
'''

    search_js = f'''
const searchData={json.dumps([{'title': m['name']+' '+m.get('nameEn',''), 'icon': m.get('icon', '🗺️'), 'url': '../maps/', 'cat': '地图'} for m in merged_maps], ensure_ascii=False)};
function doSearch(kw){{
  kw=kw.trim().toLowerCase();
  const el=document.getElementById('searchResults');
  if(!kw){{el.style.display='none';return}}
  const results=searchData.filter(s=>s.title.toLowerCase().includes(kw)).slice(0,8);
  if(!results.length){{el.style.display='block';el.innerHTML='<div class="sr-empty">未找到相关内容</div>';return}}
  el.style.display='block';
  el.innerHTML=results.map(r=>'<a href="'+r.url+'" class="sr-item"><span class="sr-icon">'+r.icon+'</span><div class="sr-body"><div class="sr-title">'+r.title+'</div><span class="sr-cat">'+r.cat+'</span></div></a>').join('');
}}
initSearch=function(){{}};
'''

    return build_page('地图攻略 | 塔科夫攻略站', '逃离塔科夫全地图攻略，包含出口、物资点、Boss位置详细标注', css, hero, content_html, js, search_js)


# ============================================================
# 5. ARTICLES listing page
# ============================================================
def build_articles_listing():
    src = open(f'{BASE}/articles.html', encoding='utf-8').read()
    css = get_page_css(src)
    hero = get_hero(src)

    cat_style = {'guide': 'cat-guide', 'weapon': 'cat-weapon', 'map': 'cat-map', 'economy': 'cat-economy', 'newbie': 'cat-newbie', 'news': 'cat-guide', 'quest': 'cat-guide'}
    cat_labels = {'weapon': '武器攻略', 'map': '地图攻略', 'guide': '通用攻略', 'economy': '经济攻略', 'newbie': '新手必看', 'news': '新闻资讯', 'quest': '任务攻略'}

    # Build article cards
    cards = []
    for a in articles_all:
        cs = cat_style.get(a.get('category', 'guide'), 'cat-guide')
        cn = a.get('categoryLabel') or cat_labels.get(a.get('category', ''), '攻略')
        views = a.get('views', 0)
        try:
            vs = f'{int(views):,}'
        except:
            vs = str(views)
        date = a.get('date') or a.get('timeAgo') or ''
        icon = a.get('icon', '📄')
        title = a['title']
        summary = a.get('summary', '')
        badge = a.get('badge', '')
        hot = badge == 'hot' or a.get('hot')
        nw = badge == 'new' or a.get('isNew')

        badges_html = ''
        if hot:
            badges_html += '<span class="badge-hot">🔥 HOT</span>'
        if nw:
            badges_html += '<span class="badge-new">✨ NEW</span>'

        cards.append(f'''<a href="{a["id"]}.html" class="art-card">
<div class="art-icon">{icon}</div>
<div class="art-body">
<div class="art-cat {cs}">{cn}</div>
<div class="art-title">{title}</div>
<div class="art-summary">{summary}</div>
<div class="art-meta">
<span>👁 {vs}</span>
<span>🕐 {date}</span>
</div>
<div class="art-badges">{badges_html}</div>
</div>
</a>''')

    grid_html = ''.join(cards)
    total = len(articles_all)

    content_html = f'''<div class="wrap">
<div class="filter-bar">
<span class="label">分类：</span>
<button class="cat-btn on" onclick="filterCat(this,'')">全部</button>
<button class="cat-btn" onclick="filterCat(this,'weapon')">🔫 武器攻略</button>
<button class="cat-btn" onclick="filterCat(this,'map')">🗺️ 地图攻略</button>
<button class="cat-btn" onclick="filterCat(this,'guide')">📖 游戏指南</button>
<button class="cat-btn" onclick="filterCat(this,'economy')">💰 经济攻略</button>
<button class="cat-btn" onclick="filterCat(this,'newbie')">🎮 新手必看</button>
<div class="search-wrap">
<span class="si">🔍</span>
<input type="text" placeholder="搜索文章..." oninput="filterSearch(this.value)" id="searchInput">
</div>
</div>
<div class="stats-bar"><span>共 <strong id="totalCount">{total}</strong> 篇文章</span></div>
<div class="articles-grid" id="articlesGrid">{grid_html}</div>
</div>'''

    js = f'''
const allArticles = {json.dumps(articles_all, ensure_ascii=False)};
const catStyle = {{'guide':'cat-guide','weapon':'cat-weapon','map':'cat-map','economy':'cat-economy','newbie':'cat-newbie','news':'cat-guide','quest':'cat-guide'}};
let currentCat=''; let currentKw='';

function renderArticles(){{
  let data=[...allArticles];
  if(currentCat) data=data.filter(a=>a.category===currentCat);
  if(currentKw) data=data.filter(a=>a.title.includes(currentKw)||(a.summary||'').includes(currentKw)||(a.tags||[]).some(t=>t.includes(currentKw)));
  document.getElementById('totalCount').textContent=data.length;
  if(!data.length){{document.getElementById('articlesGrid').innerHTML='<div class="empty"><div class="empty-icon">📭</div><div>暂无相关文章</div></div>';return;}}
  document.getElementById('articlesGrid').innerHTML=data.map(a=>{{
    const id=a.id||encodeURIComponent(a.title);
    return '<a href="'+id+'.html" class="art-card"><div class="art-icon">'+(a.icon||'📄')+'</div><div class="art-body"><div class="art-cat '+(catStyle[a.category]||'cat-guide')+'">'+(a.categoryLabel||a.categoryName||'')+'</div><div class="art-title">'+a.title+'</div><div class="art-summary">'+(a.summary||'')+'</div><div class="art-meta"><span>👁 '+(a.views||0).toLocaleString()+'</span><span>🕐 '+(a.date||a.timeAgo||'')+'</span></div><div class="art-badges">'+(a.hot||a.badge==='hot'?'<span class="badge-hot">🔥 HOT</span>':'')+(a.isNew||a.badge==='new'?'<span class="badge-new">✨ NEW</span>':'')+'</div></div></a>';
  }}).join('');
}}
function filterCat(btn,cat){{currentCat=cat;document.querySelectorAll('.cat-btn').forEach(b=>b.classList.remove('on'));btn.classList.add('on');renderArticles()}}
function filterSearch(kw){{currentKw=kw;renderArticles()}}
initSearch();renderArticles();
'''

    search_js = f'''
const searchData = {json.dumps([{'title': a['title'], 'icon': a.get('icon', '📄'), 'url': a['id']+'.html', 'cat': a.get('categoryLabel') or a.get('categoryName', '攻略')} for a in articles_all], ensure_ascii=False)};
function doSearch(kw){{
  kw=kw.trim().toLowerCase();
  const el=document.getElementById('searchResults');
  if(!kw){{el.style.display='none';return}}
  const results=searchData.filter(s=>s.title.toLowerCase().includes(kw)).slice(0,8);
  if(!results.length){{el.style.display='block';el.innerHTML='<div class="sr-empty">未找到相关内容</div>';return}}
  el.style.display='block';
  el.innerHTML=results.map(r=>'<a href="'+r.url+'" class="sr-item"><span class="sr-icon">'+r.icon+'</span><div class="sr-body"><div class="sr-title">'+r.title+'</div><span class="sr-cat">'+r.cat+'</span></div></a>').join('');
}}
initSearch=function(){{}};
'''

    return build_page('攻略文章 | 塔科夫攻略站', '逃离塔科夫攻略文章大全，包含武器、地图、经济、新手指南等全类型攻略', css, hero, content_html, js, search_js)


# ============================================================
# Generate all pages
# ============================================================
os.makedirs(f'{BASE}/ammo', exist_ok=True)
os.makedirs(f'{BASE}/loadouts', exist_ok=True)
os.makedirs(f'{BASE}/quests', exist_ok=True)
os.makedirs(f'{BASE}/maps', exist_ok=True)
os.makedirs(f'{BASE}/articles', exist_ok=True)

pages = [
    ('ammo/index.html', build_ammo()),
    ('loadouts/index.html', build_loadouts()),
    ('quests/index.html', build_quests()),
    ('maps/index.html', build_maps()),
    ('articles/index.html', build_articles_listing()),
]

for path, html_content in pages:
    full_path = f'{BASE}/{path}'
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    size = os.path.getsize(full_path)
    print(f'  {path} ({size:,} bytes)')

print(f'\nDone! Generated {len(pages)} static pages.')


# ============================================================
# Update sitemap.xml
# ============================================================
print('\nUpdating sitemap.xml...')
sitemap_path = f'{BASE}/sitemap.xml'
with open(sitemap_path, 'r', encoding='utf-8') as f:
    sitemap = f.read()

# Add new URLs for subdirectory pages
new_urls = '''
  <url>
    <loc>https://tarkov.gamewayz.com/ammo/</loc>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://tarkov.gamewayz.com/loadouts/</loc>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://tarkov.gamewayz.com/quests/</loc>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://tarkov.gamewayz.com/maps/</loc>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://tarkov.gamewayz.com/articles/</loc>
    <priority>0.9</priority>
  </url>'''

# Insert before closing </urlset>
sitemap = sitemap.replace('</urlset>', new_urls + '\n</urlset>')

with open(sitemap_path, 'w', encoding='utf-8') as f:
    f.write(sitemap)
print('  sitemap.xml updated')

# ============================================================
# Update site.json
# ============================================================
print('\nUpdating site.json...')
site_json_path = f'{BASE}/data/site.json'
with open(site_json_path, 'r', encoding='utf-8') as f:
    site = f.read()

# Fix duplicate version keys and bump to 1.5.0
site = site.replace('"version": "1.0.0",\n  "version": "1.4.0"', '"version": "1.5.0"')
site = site.replace('"text": "本站已更新至 v1.4.0', '"text": "本站已更新至 v1.5.0 · 全站已静态化')
site = site.replace('v1.4.0 · 50篇', 'v1.5.0 · 全站已静态化 · 50篇')

with open(site_json_path, 'w', encoding='utf-8') as f:
    f.write(site)
print('  site.json updated')

# ============================================================
# Bump version in all HTML files + update nav links
# ============================================================
print('\nUpdating version and nav links in all HTML files...')

# Update nav links: .html -> directory-style
def update_nav_links(html_str):
    """Update navigation links from ammo.html to ammo/ etc."""
    html_str = re.sub(r'href="ammo\.html"', 'href="ammo/"', html_str)
    html_str = re.sub(r'href="loadouts\.html"', 'href="loadouts/"', html_str)
    html_str = re.sub(r'href="quests\.html"', 'href="quests/"', html_str)
    html_str = re.sub(r'href="maps\.html"', 'href="maps/"', html_str)
    html_str = re.sub(r'href="articles\.html"', 'href="articles/"', html_str)
    return html_str

# Collect all .html files to update
html_files = []
for root, dirs, files in os.walk(BASE):
    if '.git' in root:
        continue
    for f in files:
        if f.endswith('.html'):
            html_files.append(os.path.join(root, f))

for fp in html_files:
    rel = os.path.relpath(fp, BASE)
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = False

    # Bump version
    if OLD_VER in content:
        content = content.replace(OLD_VER, NEW_VER)
        changed = True

    # Update nav links (only for root-level files, subdirectory files already have ../ prefix)
    if rel.count('/') == 0:  # root level files
        new_content = update_nav_links(content)
        if new_content != content:
            content = new_content
            changed = True

    # Also fix nav links in article subdirectory pages
    if rel.startswith('articles/') and rel != 'articles/index.html':
        # These already have ../ prefix from gen_static.py, update .html references
        pass

    if changed:
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  Updated: {rel}')

print(f'\nProcessed {len(html_files)} HTML files.')
