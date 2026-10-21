#!/usr/bin/env python3
"""Isolated subprocess fixture. This file never invokes a real ADB executable."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import sys

path = Path(os.environ['TVKIT_FIXTURE_STATE'])
state = json.loads(path.read_text())
args = sys.argv[1:]
if args[:2] != ['-s', 'fixture-device']:
    raise SystemExit('fixture refuses any other device')
args = args[2:]
if args[0] == 'pull':
    Path(args[2]).write_bytes(args[1].encode())
    print('copied fixture APK')
elif args[0] == 'shell':
    cmd = shlex.split(args[1])
    if cmd[0] == 'getprop':
        print({'ro.product.model': 'C3APRO', 'ro.build.version.sdk': '34',
               'ro.product.cpu.abilist': 'armeabi-v7a'}[cmd[1]])
    elif cmd == ['am', 'get-current-user']:
        print('0')
    elif cmd[:2] == ['wm', 'size']:
        print('Physical size: 3840x2160\nOverride size: 1920x1080')
    elif cmd[:2] == ['wm', 'density']:
        print('Physical density: 320')
    elif cmd[:2] == ['dumpsys', 'package']:
        print('User 0: installed=true hidden=false suspended=false enabled=0')
    elif cmd[:2] == ['settings', '--user']:
        print('0123456789abcdef' if cmd[-1] == 'android_id' else '1')
    elif cmd[:3] == ['cmd', 'package', 'resolve-activity']:
        print(state['home'])
    elif cmd[:3] == ['cmd', 'package', 'query-activities']:
        print('org.example.home/.Home\ncom.google.android.apps.tv.launcherx/.home.HomeActivity')
    elif cmd[:3] == ['cmd', 'package', 'set-home-activity']:
        state['writes'].append(cmd[-1])
        state['home'] = cmd[-1]
        path.write_text(json.dumps(state))
        print('Success')
    elif cmd[:2] == ['pm', 'path']:
        print('package:/data/app/base.apk\npackage:/data/app/split.apk')
    elif cmd[0] == 'sha256sum':
        print(hashlib.sha256(cmd[1].encode()).hexdigest() + ' ' + cmd[1])
    else:
        raise SystemExit('unexpected fixture shell command')
else:
    raise SystemExit('unexpected fixture command')
