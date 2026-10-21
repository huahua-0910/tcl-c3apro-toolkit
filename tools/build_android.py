#!/usr/bin/env python3
"""Build one first-party APK; never install, connect to ADB, or download dependencies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', choices=['settings-hub', 'google-policy'], required=True)
    parser.add_argument('--sdk-jar', type=Path, required=True)
    parser.add_argument('--build-tools', type=Path, required=True)
    parser.add_argument('--java-home', type=Path, required=True)
    args = parser.parse_args()
    required = [args.sdk_jar, args.java_home / 'bin/java', args.java_home / 'bin/javac',
                args.java_home / 'bin/keytool', args.build_tools / 'aapt2',
                args.build_tools / 'zipalign', args.build_tools / 'lib/d8.jar',
                args.build_tools / 'lib/apksigner.jar']
    if any(not path.is_file() for path in required):
        parser.error('Check SDK/JDK paths: a required tool is missing; no build was started.')
    app = ROOT / 'android' / args.app
    build = ROOT / 'build' / args.app
    dist = ROOT / 'dist'
    signing = ROOT / 'state' / 'signing' / args.app
    for path in [build, dist, signing]:
        path.mkdir(parents=True, exist_ok=True)
    os.chmod(signing, 0o700)
    for directory in [build / 'classes', build / 'dex']:
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir()
    env = os.environ.copy()
    env['JAVA_HOME'] = str(args.java_home.resolve())
    env['PATH'] = str(args.java_home.resolve() / 'bin') + os.pathsep + env.get('PATH', '')

    def run(*command, capture=False):
        return subprocess.run([str(x) for x in command], env=env, check=True,
                              capture_output=capture, text=True)

    password = signing / 'store-password.txt'
    key = signing / 'release.p12'
    if not key.exists():
        if not password.exists():
            fd = os.open(password, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, 'w') as stream:
                stream.write(secrets.token_hex(32) + '\n')
        run(args.java_home / 'bin/keytool', '-genkeypair', '-keystore', key,
            '-storetype', 'PKCS12', '-alias', 'toolkit', '-keyalg', 'RSA', '-keysize', '3072',
            '-validity', '3650', '-dname', 'CN=C3APRO Community Toolkit',
            '-storepass:file', password, '-keypass:file', password)
    os.chmod(key, 0o600)
    os.chmod(password, 0o600)
    bt = args.build_tools
    sdk = args.sdk_jar
    java = args.java_home / 'bin/java'
    run(bt / 'aapt2', 'compile', '--dir', app / 'res', '-o', build / 'resources.zip')
    run(bt / 'aapt2', 'link', '-I', sdk, '--manifest', app / 'AndroidManifest.xml',
        '-o', build / 'resources.apk', build / 'resources.zip')
    sources = sorted((app / 'src').rglob('*.java'))
    run(args.java_home / 'bin/javac', '-encoding', 'UTF-8', '--release', '8', '-classpath', sdk,
        '-d', build / 'classes', *sources)
    run(java, '-cp', bt / 'lib/d8.jar', 'com.android.tools.r8.D8', '--lib', sdk,
        '--min-api', '34' if args.app == 'google-policy' else '23', '--output', build / 'dex',
        *sorted((build / 'classes').rglob('*.class')))
    with zipfile.ZipFile(build / 'resources.apk', 'a', zipfile.ZIP_DEFLATED) as archive:
        archive.write(build / 'dex/classes.dex', 'classes.dex')
    run(bt / 'zipalign', '-f', '4', build / 'resources.apk', build / 'aligned.apk')
    apk = dist / (args.app + '-0.1.0.apk')
    run(java, '-jar', bt / 'lib/apksigner.jar', 'sign', '--ks', key, '--ks-key-alias', 'toolkit',
        '--ks-pass', 'file:' + str(password), '--v4-signing-enabled', 'false',
        '--out', apk, build / 'aligned.apk')
    verify = run(java, '-jar', bt / 'lib/apksigner.jar', 'verify', '--verbose', '--print-certs',
                 apk, capture=True)
    (dist / (args.app + '-signature.txt')).write_text(verify.stdout)
    inventory = [app / 'AndroidManifest.xml', *sources, *sorted((app / 'res').rglob('*.xml')),
                 Path(__file__)]
    receipt = {'app': args.app, 'version': '0.1.0', 'apk': apk.name,
               'sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
               'bytes': apk.stat().st_size, 'signature_verification': 'PASS',
               'runtime_on_tv': 'NOT_RUN_PUBLIC_PACKAGE',
               'sources': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in inventory}}
    (dist / (args.app + '-build.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
