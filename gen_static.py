import json, re, os, html

data = json.load(open('/Users/admin/Documents/test/tarkov/data/articles.json'))
articles = data['articles']

with open('/Users/admin/Documents/test/tarkov/article.html', 'r') as f:
    template = f.read()

css = re.search(r'<style>(.*?)</style>', template, re.DOTALL).group(1)
nav = re.search(r'(<nav class="nav">.*?</nav>)', template, re.DOTALL).group(1)
mobile = re.search(r'(<div class="mobile-menu".*?</div>)', template, re.DOTALL).group(1)
search = re.search(r'(<div class="search-ov".*?</div>)', template, re.DOTALL).group(1)

cs_map = {'guide': 'cat-guide', 'weapon': 'cat-weapon', 'map': 'cat-map',
          'economy': 'cat-economy', 'newbie': 'cat-newbie', 'quest': 'cat-guide', 'news': 'cat-guide'}

ga = '''<!-- Google Analytics placeholder -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-XXXXXXXXXX');
</script>'''
bd = '<meta name="baidu-site-verification" content="codeva-E78NFWmiO9" />'
gsc = '<!-- Google Search Console placeholder: replace with your verification tag -->'


def md2html(md_text):
    if not md_text:
        return '<p>暂无内容</p>'
    e = html.escape(md_text)
    e = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', e, flags=re.MULTILINE)
    e = re.sub(r'^### (.+)$', r'<h3>\1</h3>', e, flags=re.MULTILINE)
    e = re.sub(r'^## (.+)$', r'<h2>\1</h2>', e, flags=re.MULTILINE)
    e = re.sub(r'^# (.+)$', r'<h1>\1</h1>', e, flags=re.MULTILINE)
    e = re.sub(r'^---+$', r'<hr>', e, flags=re.MULTILINE)
    e = re.sub(r'^&gt; (.+)$', r'<blockquote>\1</blockquote>', e, flags=re.MULTILINE)
    e = re.sub(r'```[\w]*\n([\s\S]*?)```', r'<pre><code>\1</code></pre>', e)
    e = re.sub(r'`([^`]+)`', r'<code>\1</code>', e)
    e = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', e)
    e = re.sub(r'\*(.+?)\*', r'<em>\1</em>', e)
    e = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" target="_blank">\1</a>', e)
    e = re.sub(r'^\- (.+)$', r'<li>\1</li>', e, flags=re.MULTILINE)
    e = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', e, flags=re.MULTILINE)

    def tbl(m):
        lines = m.group(1).strip().split('\n')
        if len(lines) < 3 or not re.match(r'^\|[-:| ]+\|$', lines[1]):
            return m.group(1)
        header = [c.strip() for c in lines[0].strip('|').split('|')]
        t = '<table><thead><tr>' + ''.join('<th>' + c + '</th>' for c in header) + '</tr></thead><tbody>'
        for line in lines[2:]:
            cells = [c.strip() for c in line.strip('|').split('|')]
            t += '<tr>' + ''.join('<td>' + c + '</td>' for c in cells) + '</tr>'
        return t + '</tbody></table>'

    e = re.sub(r'^(\|.+\|(\n\|.+\|)+)', tbl, e, flags=re.MULTILINE)

    blocks = []
    for b in re.split(r'\n\n+', e):
        b = b.strip()
        if not b:
            continue
        if re.match(r'^<(h[1-6]|hr|pre|blockquote|table|ul|ol|li)', b):
            blocks.append(b)
        elif '<li>' in b:
            blocks.append('<ul>' + b + '</ul>')
        else:
            blocks.append('<p>' + b.replace('\n', '<br>') + '</p>')
    return '\n'.join(blocks)


for art in articles:
    aid = art['id']
    title = art['title']
    cat = art.get('category', 'guide')
    cl = art.get('categoryLabel') or art.get('categoryName', '攻略')
    summary = art.get('summary', '')
    tags = art.get('tags', [])
    views = art.get('views', 0)
    ds = art.get('date', art.get('timeAgo', '最近'))
    hot = art.get('badge') == 'hot'
    nw = art.get('badge') == 'new'

    related = [a for a in articles if a['id'] != aid and a.get('category') == cat][:4]
    cs = cs_map.get(cat, 'cat-guide')
    bh = ''
    if hot:
        bh += '<span class="badge-hot">🔥 HOT</span>'
    if nw:
        bh += '<span class="badge-new">✨ NEW</span>'

    rh = ''
    if related:
        items = []
        for r in related:
            rc = cs_map.get(r.get('category', 'guide'), 'cat-guide')
            rcat = r.get('categoryLabel') or r.get('categoryName', '攻略')
            rtitle = html.escape(r['title'])
            rviews = r.get('views', 0)
            rdate = r.get('date') or r.get('timeAgo', '')
            ricons = r.get('icon', '')
            items.append(
                '<a href="' + r['id'] + '.html" class="related-card">'
                '<div class="rc-cat ' + rc + '">' + rcat + '</div>'
                '<div class="rc-title">' + ricons + ' ' + rtitle + '</div>'
                '<div class="rc-meta">👁 ' + str(rviews) + ' · ' + rdate + '</div></a>'
            )
        rh = '<div class="related"><div class="related-title">📌 相关文章</div><div class="related-grid">' + ''.join(items) + '</div></div>'

    ch = md2html(art['content'])

    th = ''
    if tags:
        th = '<div class="art-tags">' + ''.join('<span class="art-tag"># ' + html.escape(t) + '</span>' for t in tags) + '</div>'

    schema_obj = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": summary,
        "datePublished": art.get('date', ''),
        "author": {"@type": "Organization", "name": "TarkovGuide"},
        "publisher": {
            "@type": "Organization",
            "name": "TarkovGuide",
            "logo": {"@type": "ImageObject", "url": "https://tarkov.gamewayz.com/favicon.ico"}
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": "https://tarkov.gamewayz.com/articles/" + aid + ".html"
        },
        "image": "https://tarkov.gamewayz.com/favicon.ico"
    }
    schema_str = json.dumps(schema_obj, ensure_ascii=False)

    esc_title = html.escape(title)
    esc_summary = html.escape(summary)
    esc_cl = html.escape(cl)

    page_parts = [
        '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n',
        '<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n',
        '<meta name="description" content="' + esc_summary + '">\n',
        '<meta property="og:title" content="' + esc_title + ' | 塔科夫攻略站">\n',
        '<meta property="og:description" content="' + esc_summary + '">\n',
        '<meta property="og:type" content="article">\n',
        '<meta property="og:url" content="https://tarkov.gamewayz.com/articles/' + aid + '.html">\n',
        '<meta property="og:image" content="https://tarkov.gamewayz.com/favicon.ico">\n',
        '<meta name="twitter:card" content="summary_large_image">\n',
        '<link rel="canonical" href="https://tarkov.gamewayz.com/articles/' + aid + '.html">\n',
        '<title>' + esc_title + ' | 塔科夫攻略站</title>\n',
        bd + '\n',
        gsc + '\n',
        ga + '\n',
        '<script type="application/ld+json">\n' + schema_str + '\n</script>\n',
        '<style>' + css + '</style>\n</head>\n<body>\n',
        nav + '\n',
        mobile + '\n',
        search + '\n',
        '<div class="container">\n',
        '  <div class="breadcrumb">\n    <a href="../index.html">首页</a>\n    <span class="sep">›</span>\n    <a href="../articles.html">攻略文章</a>\n    <span class="sep">›</span>\n    <span>' + esc_cl + '</span>\n  </div>\n',
        '  <div class="art-header">\n    <div class="art-category ' + cs + '">' + esc_cl + '</div>\n',
        '    <h1 class="art-h1">' + esc_title + '</h1>\n',
        '    <div class="art-meta">\n      <span class="meta-item">👁 ' + str(views) + ' 次阅读</span>\n',
        '      <span class="meta-item">🕐 ' + str(ds) + '</span>\n',
        '      <span class="meta-item">✍️ 塔科夫攻略站</span>\n',
        '      ' + bh + '\n    </div>\n  </div>\n',
        '  <div class="art-content">' + ch + '</div>\n',
        th + '\n',
        rh + '\n',
        '  <a href="../articles.html" class="back-btn">← 返回攻略列表</a>\n</div>\n',
        '<footer class="footer">\n  <div class="footer-inner">\n',
        '    <span>© 2024-2026 TarkovGuide · <a href="../index.html">返回首页</a></span>\n',
        '    <span><a href="../privacy.html">隐私政策</a> · <a href="../terms.html">服务条款</a> · <a href="../about.html">关于我们</a></span>\n',
        '  </div>\n</footer>\n</body>\n</html>',
    ]
    page = ''.join(page_parts)

    with open('/Users/admin/Documents/test/tarkov/articles/' + aid + '.html', 'w', encoding='utf-8') as f:
        f.write(page)
    print(f'  {aid}.html')

print(f'\nDone! Generated {len(articles)} static pages.')
