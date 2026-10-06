"""Fetch the public GitHub calendar and render a self-contained animated SVG.

No PAT, external widgets, or third-party Python dependencies are required.
"""
import argparse
import datetime as dt
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USERNAME = 'd11fy'
COLORS = ['#172433', '#104039', '#16745b', '#21b881', '#79f2be']


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.tooltips = {}
        self.active = None
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'data-date' in a and 'data-level' in a:
            self.cells[a.get('id', a['data-date'])] = {
                'date': a['data-date'], 'level': int(a['data-level']),
                'count': int(a['data-count']) if 'data-count' in a else None,
            }
        if tag == 'tool-tip' and a.get('for'):
            self.active = a['for']
            self.buffer = []

    def handle_data(self, data):
        if self.active:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == 'tool-tip' and self.active:
            self.tooltips[self.active] = ''.join(self.buffer).strip()
            self.active = None


def parse_calendar(source):
    parser = CalendarParser()
    parser.feed(source)
    days = []
    for cell_id, cell in parser.cells.items():
        label = parser.tooltips.get(cell_id, '')
        if cell['count'] is None:
            match = re.search(r'\b([\d,]+)\s+contributions?\b', label, re.I)
            if match:
                cell['count'] = int(match.group(1).replace(',', ''))
            elif re.search(r'\bNo contributions\b', label, re.I):
                cell['count'] = 0
            else:
                raise ValueError(f'Missing contribution count for {cell["date"]}')
        dt.date.fromisoformat(cell['date'])
        if not 0 <= cell['level'] <= 4 or cell['count'] < 0:
            raise ValueError('Invalid contribution cell')
        days.append(cell)
    days.sort(key=lambda d: d['date'])
    if len(days) < 350 or len({d['date'] for d in days}) != len(days):
        raise ValueError('Incomplete contribution calendar; keeping the previous artwork')
    for before, after in zip(days, days[1:]):
        if dt.date.fromisoformat(after['date']) - dt.date.fromisoformat(before['date']) != dt.timedelta(days=1):
            raise ValueError('Contribution calendar contains a date gap')
    return days


def stats(days):
    longest = running = 0
    for day in days:
        running = running + 1 if day['count'] else 0
        longest = max(longest, running)
    eligible = [d for d in days if d['date'] <= dt.date.today().isoformat()]
    if eligible and eligible[-1]['date'] == dt.date.today().isoformat() and not eligible[-1]['count']:
        eligible.pop()
    streak = 0
    for day in reversed(eligible):
        if not day['count']:
            break
        streak += 1
    return {'total': sum(d['count'] for d in days), 'active_days': sum(bool(d['count']) for d in days),
            'longest_streak': longest, 'current_streak': streak}


def render(days):
    first = dt.date.fromisoformat(days[0]['date'])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    last = dt.date.fromisoformat(days[-1]['date'])
    columns = (last - start).days // 7 + 1
    step = min(14, 760 / columns)
    box = step - 3
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="860" height="270" viewBox="0 0 860 270" role="img" aria-labelledby="title desc">',
             '<title id="title">Ali Sohail — GitHub contributions</title>',
             f'<desc id="desc">Public contribution calendar for {USERNAME}, {days[0]["date"]} through {days[-1]["date"]}.</desc>',
             '<rect x="1" y="1" width="858" height="268" rx="18" fill="#0b121c" stroke="#223041"/>',
             '<style>text{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}.day{animation:reveal .5s ease-out both}@keyframes reveal{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}@media(prefers-reduced-motion:reduce){.day{animation:none}}</style>',
             '<circle cx="26" cy="25" r="4" fill="#79f2be"/><text x="40" y="30" fill="#79f2be" font-size="12">d11fy@github:~$ ./contributions</text>',
             '<text x="832" y="30" text-anchor="end" fill="#71869d" font-size="10">PUBLIC ACTIVITY / DAILY SYNC</text>']
    month = None
    for day in days:
        date = dt.date.fromisoformat(day['date'])
        offset = (date - start).days
        col, row = divmod(offset, 7)
        x, y = 60 + col * step, 78 + row * 14
        if date.month != month and row == 0:
            parts.append(f'<text x="{x:.1f}" y="64" fill="#71869d" font-size="10">{date:%b}</text>')
            month = date.month
        tip = html.escape(f'{day["date"]}: {day["count"]} contributions')
        parts.append(f'<rect class="day" x="{x:.1f}" y="{y}" width="{box:.1f}" height="11" rx="2" fill="{COLORS[day["level"]]}" style="animation-delay:{(col*.017+row*.035):.3f}s"><title>{tip}</title></rect>')
    for row, label in [(1, 'Mon'), (3, 'Wed'), (5, 'Fri')]:
        parts.append(f'<text x="24" y="{87+row*14}" fill="#71869d" font-size="10">{label}</text>')
    parts.append('<text x="680" y="194" fill="#71869d" font-size="9">Less</text>')
    for i, color in enumerate(COLORS):
        parts.append(f'<rect x="{710+i*14}" y="185" width="10" height="10" rx="2" fill="{color}"/>')
    parts.append('<text x="784" y="194" fill="#71869d" font-size="9">More</text>')
    s = stats(days)
    parts.append('<path d="M24 211H836" stroke="#223041"/>')
    values = [(24, f'{s["total"]:,} contributions'), (265, f'{s["active_days"]} active days'),
              (475, f'{s["longest_streak"]}d longest streak'), (704, f'{s["current_streak"]}d current')]
    for x, value in values:
        parts.append(f'<text x="{x}" y="240" fill="#d8e3ef" font-size="12">{value}</text>')
    parts.append('</svg>')
    return '\n'.join(parts) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--html', type=Path, help='Parse a previously downloaded calendar')
    args = ap.parse_args()
    if args.html:
        source = args.html.read_text()
    else:
        req = urllib.request.Request(f'https://github.com/users/{USERNAME}/contributions',
                                     headers={'User-Agent': 'd11fy-profile-art', 'Accept': 'text/html'})
        with urllib.request.urlopen(req, timeout=45) as response:
            source = response.read().decode('utf-8')
    days = parse_calendar(source)
    artwork = render(days)
    data = {'username': USERNAME, 'period': [days[0]['date'], days[-1]['date']], 'stats': stats(days), 'days': days}
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'assets').mkdir(exist_ok=True)
    (ROOT / 'data/contributions.json').write_text(json.dumps(data, indent=2) + '\n')
    (ROOT / 'assets/contributions.svg').write_text(artwork)
    print(f'Rendered {len(days)} days and {data["stats"]["total"]:,} contributions for {USERNAME}')


if __name__ == '__main__':
    main()
