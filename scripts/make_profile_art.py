"""Generate the portrait and information card; Pillow is needed only here."""
import html
from pathlib import Path
import sys
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]


def frame(width, title, description):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="360" viewBox="0 0 {width} 360" role="img" aria-labelledby="title desc">',
            f'<title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(description)}</desc>',
            f'<rect x="1" y="1" width="{width-2}" height="358" rx="18" fill="#0b121c" stroke="#223041"/>',
            '<style>text{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}.line{animation:enter .5s ease both}@keyframes enter{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}@media(prefers-reduced-motion:reduce){.line{animation:none}.portrait text{clip-path:none}}</style>',
            '<circle cx="24" cy="24" r="4" fill="#ff6b6b"/><circle cx="39" cy="24" r="4" fill="#e9b45c"/><circle cx="54" cy="24" r="4" fill="#79f2be"/>']


def portrait(path):
    image = Image.open(path).convert('RGB')
    # The current public avatar has a solid blue background. Treat those pixels
    # as whitespace in the character grid; do not publish an edited raster.
    pixels = []
    for r, g, b in list(image.get_flattened_data()) if hasattr(image, 'get_flattened_data') else list(image.getdata()):
        background = b > 100 and b > r * 1.5 and b > g * 1.45
        pixels.append(255 if background else round(.299*r + .587*g + .114*b))
    grayscale = Image.new('L', image.size)
    grayscale.putdata(pixels)
    grayscale = ImageOps.autocontrast(grayscale, cutoff=1)
    height = round(74 * image.height / image.width * 3.8 / 5.1)
    if height > 56:
        image_height = 56
        image_width = round(image_height * image.width / image.height * 5.1 / 3.8)
    else:
        image_height, image_width = height, 74
    grayscale = grayscale.resize((image_width, image_height), Image.Resampling.LANCZOS)
    ramp = ' .`:-=+*cs#%@'
    rows = [''.join(ramp[round((255-grayscale.getpixel((x,y)))/255*(len(ramp)-1))]
                    for x in range(image_width)) for y in range(image_height)]
    out = frame(330, 'Ali Sohail — animated ASCII portrait',
                'Monochrome ASCII rendering of Ali Sohail’s public GitHub avatar. Rows reveal once on load.')
    out.append('<text x="306" y="28" text-anchor="end" fill="#71869d" font-size="10">portrait.ascii</text>')
    out.append('<defs>')
    for y in range(len(rows)):
        delay = y * .03
        duration = delay + .25
        hold = delay / duration
        out.append(f'<clipPath id="r{y}"><rect x="20" y="{47+y*5.1:.1f}" width="290" height="6"><animate attributeName="width" values="0;0;290" keyTimes="0;{hold:.5f};1" begin="0s" dur="{duration:.3f}s" fill="freeze"/></rect></clipPath>')
    out.append('</defs><g class="portrait" fill="#d8e3ef" font-family="monospace" font-size="6.4">')
    for y, row in enumerate(rows):
        out.append(f'<text x="20" y="{52+y*5.1:.1f}" xml:space="preserve" clip-path="url(#r{y})">{html.escape(row)}</text>')
    out.extend(['</g>', '<text x="165" y="342" text-anchor="middle" fill="#79f2be" font-size="10">ALI SOHAIL / d11fy</text>', '</svg>'])
    (ROOT / 'assets/portrait.svg').write_text('\n'.join(out) + '\n')


def info_card():
    out = frame(530, 'Ali Sohail — software developer',
                'Software developer in Palestine. Builds web applications, AI integrations, CRM systems, and workflow automation.')
    out.append('<text x="506" y="28" text-anchor="end" fill="#71869d" font-size="10">ali@github ~</text>')
    out.extend(['<text class="line" x="26" y="76" fill="#eef5ff" font-size="29" font-weight="700">Ali Sohail</text>',
                '<text class="line" x="27" y="101" fill="#79f2be" font-size="13" style="animation-delay:.1s">Software Developer &amp; Digital Entrepreneur</text>',
                '<path d="M26 119H504" stroke="#223041"/>'])
    rows = [('Based', 'Palestine'), ('Focus', 'Web apps · AI integrations · Automation'),
            ('Build', 'CRM systems &amp; digital commerce'), ('Stack', 'TypeScript · React · Next.js · Python'),
            ('Data', 'PostgreSQL · APIs · RAG'), ('Now', 'Nursing AI · Alosh Store · Subbyte')]
    for i, (label, value) in enumerate(rows):
        y = 151+i*27
        out.append(f'<g class="line" style="animation-delay:{.2+i*.1:.1f}s"><text x="27" y="{y}" fill="#71869d" font-size="12">{label}</text><text x="105" y="{y}" fill="#d8e3ef" font-size="12">{value}</text></g>')
    out.extend(['<path d="M26 311H504" stroke="#223041"/>',
                '<text class="line" x="27" y="339" fill="#79f2be" font-size="11" style="animation-delay:.9s">$ turning ideas into useful software<tspan fill="#eef5ff"> ▋</tspan></text>', '</svg>'])
    (ROOT / 'assets/info-card.svg').write_text('\n'.join(out) + '\n')


if __name__ == '__main__':
    (ROOT / 'assets').mkdir(exist_ok=True)
    portrait(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'data/avatar.png')
    info_card()
