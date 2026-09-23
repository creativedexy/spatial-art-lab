"""Write a DaVinci Resolve timeline (FCPXML 1.10) from rendered shots, so an edit arrives ready-built.

    python3 experiments/004-specimen-studio/timeline.py out.fcpxml shot1.mp4 shot2.mp4 ... [--audio bed.wav] [--name "Spider piece"]

Resolve: File > Import > Timeline > pick the .fcpxml (media is linked by absolute path, nothing is copied).
Each shot becomes a clip on V1 in order, with a marker carrying its name; an optional music bed sits
under the whole run as a connected clip on A2. Frame size and rate come from the first shot (ffprobe).
Resolve free cannot be scripted from outside, so a timeline file is the headless hand-off.
"""
import json, subprocess, sys
from fractions import Fraction
from pathlib import Path
from xml.sax.saxutils import escape


def probe(p):
    r = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(p)], capture_output=True, text=True).stdout)
    v = next((s for s in r['streams'] if s['codec_type'] == 'video'), None)
    a = next((s for s in r['streams'] if s['codec_type'] == 'audio'), None)
    return v, a, float(r['format']['duration'])


def t(frames, fps):                                     # rational time in FCPXML form, e.g. 96/24s
    f = Fraction(frames, 1) / fps
    return f'{f.numerator}/{f.denominator}s' if f.denominator != 1 else f'{f.numerator}s'


def main(argv):
    audio = argv[argv.index('--audio') + 1] if '--audio' in argv else None
    name = argv[argv.index('--name') + 1] if '--name' in argv else 'Spider piece'
    skip = {audio, name, '--audio', '--name'}
    out, shots = Path(argv[0]), [Path(a).resolve() for a in argv[1:] if a not in skip]
    v0, _, _ = probe(shots[0]); fps = Fraction(v0['r_frame_rate'])
    W, H = v0['width'], v0['height']
    res = [f'<format id="r0" name="FFVideoFormat{H}p{int(fps)}" frameDuration="{t(1, fps)}" width="{W}" height="{H}"/>']
    spine, offset = [], 0
    for i, s in enumerate(shots, 1):
        v, a, dur = probe(s); n = int(round(dur * fps))
        res.append(f'<asset id="r{i}" name="{escape(s.stem)}" start="0s" duration="{t(n, fps)}" hasVideo="1" format="r0"'
                   + (f' hasAudio="1" audioSources="1" audioChannels="{a["channels"]}" audioRate="{a["sample_rate"]}"' if a else '')
                   + f'><media-rep kind="original-media" src="{escape(s.as_uri())}"/></asset>')
        spine.append([f'<asset-clip ref="r{i}" name="{escape(s.stem)}" offset="{t(offset, fps)}" start="0s" duration="{t(n, fps)}" format="r0" tcFormat="NDF">',
                      f'<marker start="0s" duration="{t(1, fps)}" value="{escape(s.stem)}"/>', '</asset-clip>'])
        offset += n
    if audio:                                          # music bed: connected clip under the first shot, spanning the run
        ap = Path(audio).resolve(); _, a, adur = probe(ap); an = min(offset, int(adur * fps)); k = len(shots) + 1
        res.append(f'<asset id="r{k}" name="{escape(ap.stem)}" start="0s" duration="{t(int(adur * fps), fps)}" hasAudio="1" audioSources="1"'
                   f' audioChannels="{a["channels"]}" audioRate="{a["sample_rate"]}"><media-rep kind="original-media" src="{escape(ap.as_uri())}"/></asset>')
        spine[0].insert(2, f'<asset-clip ref="r{k}" lane="-1" name="{escape(ap.stem)}" offset="0s" start="0s" duration="{t(an, fps)}" audioRole="music"/>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n<fcpxml version="1.10">\n<resources>\n' + '\n'.join(res) + '\n</resources>\n'
           f'<library><event name="{escape(name)}"><project name="{escape(name)}">\n'
           f'<sequence format="r0" duration="{t(offset, fps)}" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k"><spine>\n'
           + '\n'.join(''.join(c) for c in spine) + '\n</spine></sequence></project></event></library>\n</fcpxml>\n')
    out.write_text(xml)
    print(f'{out}: {len(shots)} shots, {offset} frames ({offset / fps:.1f}s) at {W}x{H} {float(fps):g} fps' + (f', bed {Path(audio).name}' if audio else ''))


if __name__ == '__main__':
    main(sys.argv[1:])
