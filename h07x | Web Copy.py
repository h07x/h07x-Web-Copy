import sys
import os
import urllib.request
import urllib.parse
import urllib.error
import ssl
import webbrowser
from html.parser import HTMLParser
from html import escape
import socket
import random
import re
import io
import zipfile
import time
import http.cookiejar
from http.server import HTTPServer, BaseHTTPRequestHandler

def getfreeport():
    while True:
        port = random.randint(1024, 65535)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                continue

def sanitise(name, allowdot=False):
    if allowdot:
        cleaned = re.sub(r'[^a-z0-9.]', '', name.lower())
    else:
        cleaned = re.sub(r'[^a-z0-9]', '', name.lower())
    cleaned = re.sub(r'\.+', '.', cleaned).strip('.')
    return cleaned if cleaned else 'file'

def fetchurlsimple(url):
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            content = resp.read().decode('utf-8', errors='replace')
            contenttype = resp.headers.get('Content-Type', '')
            return content, contenttype, None
    except Exception as e:
        return None, None, str(e)

def fetchurladvanced(url):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    useragents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    ]
    for attempt in range(3):
        headers = {'User-Agent': random.choice(useragents)}
        try:
            req = urllib.request.Request(url, headers=headers)
            with opener.open(req, context=ctx, timeout=30) as resp:
                content = resp.read().decode('utf-8', errors='replace')
                contenttype = resp.headers.get('Content-Type', '')
                if len(content) < 500 and 'captcha' in content.lower():
                    continue
                return content, contenttype
        except Exception:
            if attempt == 2:
                return None, 'advanced fetch failed'
            time.sleep(2 ** attempt)
    return None, 'max retries'

def fetchurl(url):
    content, ctype, err = fetchurlsimple(url)
    if content is not None:
        if len(content) > 500 or ('captcha' not in content.lower() and 'block' not in content.lower()):
            return content, ctype
    print('  switching to advanced fetch...')
    return fetchurladvanced(url)

def downloadasset(asseturl):
    content, _ = fetchurl(asseturl)
    if content is None:
        alturl = asseturl.replace('http://', 'https://') if asseturl.startswith('http://') else asseturl.replace('https://', 'http://')
        if alturl != asseturl:
            print(f'  retrying with alternate protocol for {asseturl}')
            content, _ = fetchurl(alturl)
    return content

class ultimateextractor(HTMLParser):
    def __init__(self, baseurl):
        super().__init__()
        self.baseurl = baseurl
        self.assets = []
        self.possiblecss = []
    def handle_starttag(self, tag, attrs):
        attrdict = dict(attrs)
        if tag == 'link' and attrdict.get('rel') == 'stylesheet' and 'href' in attrdict:
            href = attrdict['href']
            absolute = urllib.parse.urljoin(self.baseurl, href)
            self.assets.append({
                'tag': 'link',
                'attr': 'href',
                'original': href,
                'url': absolute
            })
        elif tag == 'script' and 'src' in attrdict:
            src = attrdict['src']
            absolute = urllib.parse.urljoin(self.baseurl, src)
            self.assets.append({
                'tag': 'script',
                'attr': 'src',
                'original': src,
                'url': absolute
            })
        if tag == 'link' and 'href' in attrdict and '.css' in attrdict['href']:
            href = attrdict['href']
            absolute = urllib.parse.urljoin(self.baseurl, href)
            if absolute not in [a['url'] for a in self.assets]:
                self.assets.append({
                    'tag': 'link',
                    'attr': 'href',
                    'original': href,
                    'url': absolute
                })
    def handle_data(self, data):
        csslinks = re.findall(r'https?://[^\s\'"`<>]+\.css', data)
        for link in csslinks:
            self.possiblecss.append(link)
        jscss = re.findall(r'["\']([^\s\'"`<>]+\.css)["\']', data)
        for link in jscss:
            absolute = urllib.parse.urljoin(self.baseurl, link)
            self.possiblecss.append(absolute)

class ultimaterewriter(HTMLParser):
    def __init__(self, baseurl, assetmap):
        super().__init__()
        self.baseurl = baseurl
        self.assetmap = assetmap
        self.result = []
    def handle_starttag(self, tag, attrs):
        newattrs = []
        for name, value in attrs: 
            if tag == 'link' and name == 'href' and value in self.assetmap:
                newattrs.append((name, self.assetmap[value]))
            elif tag == 'script' and name == 'src' and value in self.assetmap:
                newattrs.append((name, self.assetmap[value]))
            else:
                newattrs.append((name, value))
        attrstr = '' if not newattrs else ' ' + ' '.join(f'{k}="{v}"' for k, v in newattrs if v)
        self.result.append(f'<{tag}{attrstr}>')
    def handle_endtag(self, tag):
        self.result.append(f'</{tag}>')
    def handle_data(self, data):
        self.result.append(data)
    def handle_comment(self, data):
        pass
    def handle_decl(self, decl):
        self.result.append(f'<!{decl}>')
    def get_html(self):
        return ''.join(self.result)

def wrapashtml(rawcontent, contenttype, originalurl):
    escaped = escape(rawcontent)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloned: {originalurl}</title>
    <style>
        body {{ background: #0a0c15; color: #e2e8f0; font-family: monospace; padding: 2rem; margin: 0; }}
        pre {{ white-space: pre-wrap; word-wrap: break-word; background: #111827; padding: 1rem; border-radius: 12px; }}
        .info {{ background: #1e293b; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }}
        a {{ color: #60a5fa; }}
    </style>
</head>
<body>
<div class="info">
    <strong>Cloned from:</strong> <a href="{originalurl}" target="_blank">{originalurl}</a><br>
    <strong>Original type:</strong> {contenttype}
</div>
<pre>{escaped}</pre>
</body>
</html>"""

def clonewebsiteinmemory(url, mode):
    print(f'cloning: {url}')
    content, contenttype = fetchurl(url)
    if content is None:
        print(f'error: {contenttype}')
        return None
    files = {}
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.netloc or parsed.path.split('/')[0]
    if mode == '1':
        if 'text/html' in contenttype.lower():
            finalhtml = content
        else:
            finalhtml = wrapashtml(content, contenttype, url)
        basename = sanitise(hostname, allowdot=True)
        filename = basename + '.html'
        files[filename] = finalhtml
        return files, filename
    else:
        if 'text/html' not in contenttype.lower():
            finalhtml = wrapashtml(content, contenttype, url)
            basename = sanitise(hostname, allowdot=True)
            filename = basename + '.html'
            files[filename] = finalhtml
            return files, filename
        extractor = ultimateextractor(url)
        extractor.feed(content)
        assets = extractor.assets
        possiblecss = extractor.possiblecss
        for cssurl in possiblecss:
            if not any(a['url'] == cssurl for a in assets):
                assets.append({
                    'tag': 'link',
                    'attr': 'href',
                    'original': cssurl,
                    'url': cssurl
                })
        assetmap = {}
        for asset in assets:
            asseturl = asset['url']
            originalvalue = asset['original']
            ext = '.css' if asset['tag'] == 'link' else '.js'
            if not asseturl.endswith(ext) and ext == '.css':
                if '.css' in asseturl:
                    ext = '.css'
            pathpart = urllib.parse.urlparse(asseturl).path
            if pathpart and '/' in pathpart:
                base = os.path.basename(pathpart)
            else:
                base = asseturl.split('?')[0].split('#')[0]
            if not base or '.' not in base:
                base = asset['tag'] + ext
            base = sanitise(base, allowdot=True)
            if not base.endswith(ext):
                base += ext
            finalname = base
            counter = 1
            while finalname in files:
                namenoext, oldext = os.path.splitext(base)
                finalname = f'{namenoext}{counter}{oldext}'
                counter += 1
            print(f'  downloading {asset["tag"]}: {asseturl}')
            assetcontent = downloadasset(asseturl)
            if assetcontent is not None:
                files[finalname] = assetcontent
                assetmap[originalvalue] = finalname
            else:
                print(f'  failed: {asseturl}')
        rewriter = ultimaterewriter(url, assetmap)
        rewriter.feed(content)
        finalhtml = rewriter.get_html()
        path = parsed.path
        if not path or path == '/':
            mainbase = 'index'
        else:
            raw = path.lstrip('/').replace('/', '.')
            mainbase = sanitise(raw, allowdot=True)
            if not mainbase:
                mainbase = 'index'
        mainfilename = mainbase + '.html'
        files[mainfilename] = finalhtml
        txtfilename = mainbase + '.txt'
        files[txtfilename] = finalhtml
        return files, mainfilename

class memoryhandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.files = kwargs.pop('files', {})
        self.mainfile = kwargs.pop('mainfile', 'index.html')
        super().__init__(*args, **kwargs)
    def do_GET(self):
        path = self.path.lstrip('/')
        if path == '' or path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>web cloner by h07x</title></head>
<body style="background:#0a0c15;color:#e2e8f0;font-family:sans-serif;text-align:center;padding:2rem;">
<h1>web cloner by x07x</h1>
<p>choose an option:</p>
<div style="margin:2rem;">
    <a href="/{self.mainfile}" style="display:inline-block;background:#3b82f6;color:white;padding:12px 24px;margin:0 10px;border-radius:8px;text-decoration:none;">preview</a>
    <button onclick="location.href='/download'" style="background:#10b981;color:white;padding:12px 24px;margin:0 10px;border:none;border-radius:8px;cursor:pointer;">download zip</button>
</div>
</body>
</html>'''
            self.wfile.write(html.encode())
        elif path == 'download':
            zipbuf = io.BytesIO()
            with zipfile.ZipFile(zipbuf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for fname, content in self.files.items():
                    zf.writestr(fname, content)
            zipbuf.seek(0)
            self.send_response(200)
            self.send_header('Content-Type', 'application/zip')
            self.send_header('Content-Disposition', 'attachment; filename="webclone.zip"')
            self.end_headers()
            self.wfile.write(zipbuf.getvalue())
        else:
            if path in self.files:
                content = self.files[path]
                if path.endswith('.css'):
                    ctype = 'text/css'
                elif path.endswith('.js'):
                    ctype = 'application/javascript'
                else:
                    ctype = 'text/html'
                self.send_response(200)
                self.send_header('Content-type', ctype)
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'file not found')
    def log_message(self, format, *args):
        pass

def startserver(files, mainfile, port):
    handler = lambda *args, **kwargs: memoryhandler(*args, files=files, mainfile=mainfile, **kwargs)
    with HTTPServer(('', port), handler) as httpd:
        url = f'http://localhost:{port}'
        print(f'\npreview link: {url}/{mainfile}')
        print(f'download page: {url}')
        print('press ctrl+c to stop\n')
        webbrowser.open(url)
        httpd.serve_forever()

def main():
    print('-' * 55)
    print('   web cloner by x07x')
    print('-' * 55)
    url = input('\nenter website url: ').strip()
    if not url:
        print('no url entered.')
        return
    mode = input('\nsave as (1) single html file or (2) separated files? (1/2): ').strip()
    if mode not in ('1', '2'):
        print('invalid choice, using single file.')
        mode = '1'
    print('\n' + '-' * 55)
    result = clonewebsiteinmemory(url, mode)
    if result is None:
        return
    files, mainfile = result
    print('-' * 55)
    csscount = sum(1 for f in files if f.endswith('.css'))
    jscount = sum(1 for f in files if f.endswith('.js'))
    print(f'\ncloned: {len(files)} files total (css: {csscount}, js: {jscount}, html: 1)')
    port = getfreeport()
    try:
        startserver(files, mainfile, port)
    except KeyboardInterrupt:
        print('\n\nserver stopped.')
    except Exception as e:
        print(f'\nerror: {e}')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\nstopped.')