"""Make a .toe whose Execute DAT runs a Python file on start. usage: mktoe.py out.toe script.py"""
import sys, struct, shutil, subprocess, os
out, script = sys.argv[1], os.path.abspath(sys.argv[2])
base = '/Applications/TouchDesigner.app/Contents/Resources/tfs/Samples/Setup/Base/NewProject.toe'
tmp = out[:-4] + '-src.toe'; shutil.rmtree(tmp + '.dir', ignore_errors=True)
shutil.copy(base, tmp)
subprocess.run(['/Applications/TouchDesigner.app/Contents/MacOS/toeexpand', tmp], capture_output=True)
d = tmp + '.dir'
proj = next(p for p in os.listdir(d) if p.endswith('.n') and p not in ('perform.n',) and not p.startswith('.'))[:-2]
os.makedirs(f'{d}/{proj}', exist_ok=True)
open(f'{d}/{proj}/boot.n', 'w').write('DAT:execute\ntile 0 0 130 90\nflags =  viewer 1 parlanguage 0\nend\n')
open(f'{d}/{proj}/boot.parm', 'w').write('?\nstart 0 on\nlanguage 0 python\n?\n')
log = script + '.log'
code = (f"def onStart():\n"
        f"    import traceback\n"
        f"    open({log!r}, 'w').write('started\\n')\n"
        f"    try:\n"
        f"        exec(open({script!r}).read(), globals())\n"
        f"    except Exception:\n"
        f"        open({log!r}, 'a').write(traceback.format_exc())\n"
        f"    return\n").encode()
open(f'{d}/{proj}/boot.text', 'wb').write(b'2\n*' + struct.pack('>5i', 1, 1, 1, 1, 2) + struct.pack('>i', len(code)) + code)
toc = open(tmp + '.toc').read().splitlines()
toc += [f'{proj}/boot.n', f'{proj}/boot.parm', f'{proj}/boot.text']
open(tmp + '.toc', 'w').write('\n'.join(toc) + '\n')
subprocess.run(['/Applications/TouchDesigner.app/Contents/MacOS/toecollapse', tmp], capture_output=True)
shutil.move(tmp, out); print('made', out, 'project comp:', proj)
