#!/usr/bin/env python3
import argparse
import os
import shlex
import subprocess
import sys


# The threshold for --images-sleep's automatic calculation, where it'll decide
# whether or not to sleep for 0s or 1s.
# https://wm-bot.wmcloud.org/logs/%23miraheze-tech-ops/20250714.txt#:~:text=[05:37:19],That's%20sensible
_IMAGES_SLEEP_AUTO_THRESHOLD = 1000


def parse_args(input_args: list | None = None, check_paths: bool = True) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='A script to automate manual wiki imports')
    parser.add_argument(
        '--no-log', dest='nolog', action='store_true',
        help='Whether or not to disable logging to the server admin log',
    )
    parser.add_argument(
        '--confirm', '--yes', '-y', dest='confirm', action='store_true',
        help='Whether or not to skip the initial confirmation prompt',
    )
    parser.add_argument('--version', help='MediaWiki version to use (automatically detected if not passed)')
    parser.add_argument('--xml', help='XML file to import')
    parser.add_argument('--username-prefix', help='Interwiki prefix for importing XML')
    parser.add_argument('--images', help='Directory of images to import')
    parser.add_argument(
        '--images-comment', help='The comment passed to importImages.php'
        ' (example: "Importing images from https://example.com ([[phorge:T1234|T1234]])")',
    )
    parser.add_argument(
        '--search-recursively', action='store_true',
        help='Whether or not to pass --search-recursively (check files in subdirectories) to importImages.php',
    )
    parser.add_argument(
        '--images-sleep', type=int, default=-1,
        help='The time to sleep between importing images for importImages.php (negative for auto-calculation)',
    )
    parser.add_argument('wiki', help='Database name of the wiki to import to')

    args = parser.parse_args(input_args)
    if not args.xml and not args.images:
        raise ValueError('--xml and/or --images must be passed')
    if args.images and not args.images_comment:
        raise ValueError('--images-comment must be passed when importing images')

    # This is honestly only for unit testing as I can't really think of a reason
    # to disable this check in production
    if check_paths:
        # This is not meant to be comprehensive, but just to make sure that someone
        # doesn't typo a path or so
        if args.xml and not os.path.exists(args.xml):
            raise ValueError(f'Cannot find XML to import: {repr(args.xml)}')
        if args.images and not os.path.exists(args.images):
            raise ValueError(f'Cannot find images to import: {repr(args.images)}')

    if args.images and args.images_sleep < 0:
        args.images_sleep = calculate_images_sleep(args.images) if check_paths else 0

    return args


def calculate_images_sleep(images: str) -> int:
    # In the interest of code simplicity, all calculations are done assuming that
    # --search-recursively is passed. It is unlikely where one wants to only upload
    # files from a directory but not its subdirectories anyway, and this is meant
    # to be a "eh, good enough" heuristic, so an "eh, good enough" algorithm for
    # edge cases seems acceptable.
    total = 0

    for _, _, files in os.walk(images):
        total += len(files)
        if total >= _IMAGES_SLEEP_AUTO_THRESHOLD:
            return 1

    return 0


def log(message: str):  # pragma: no cover
    subprocess.run(
        ['/usr/local/bin/logsalmsg', message],
        check=True,
    )


def get_version(wiki: str) -> str:  # pragma: no cover
    return subprocess.run(
        ['/usr/local/bin/getMWVersion', wiki],
        stdout=subprocess.PIPE,
        check=True,
        text=True,
    ).stdout.strip()


def get_scripts(args: argparse.Namespace) -> list[list[str]]:
    scripts = []

    if args.xml:
        script = ['importDump', '--no-updates']
        if args.username_prefix:
            script.append(f'--username-prefix={args.username_prefix}')
        script.extend(['--', args.xml])
        scripts.append(script)

    if args.images:
        script = ['importImages', f'--sleep={args.images_sleep}', f'--comment={args.images_comment}']
        if args.search_recursively:
            script.append('--search-recursively')
        script.extend(['--', args.images])
        scripts.append(script)

    if args.xml:
        scripts.append(['rebuildall'])
        scripts.append(['initEditCount'])

    scripts.append(['initSiteStats', '--update'])

    version = args.version or get_version(args.wiki)
    scripts = [
        # This is a hack to squeeze the --wiki argument after the script name, but before any of the other arguments
        # (adding --wiki to every script manually is kinda clutters the whole list since most maintenance scripts
        # run on a single wiki, and all of the ones used here also run on a single wiki)
        ['sudo', '-u', 'www-data', 'php', f'/srv/mediawiki/{version}/maintenance/run.php', script[0], f'--wiki={args.wiki}', *script[1:]] for script in scripts
    ]
    return scripts


def run_scripts(args: argparse.Namespace, scripts: list[list[str]]) -> int:  # pragma: no cover
    for script in scripts:
        print(f'Running {shlex.join(script)}')
        if not args.nolog:
            print('Logging execution...')
            log(f'{shlex.join(script)} (START)')

        proc = subprocess.Popen(script)
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            proc.wait()

        if not args.nolog:
            print('Logging execution end...')
            log(f'{shlex.join(script)} (END - exit={proc.returncode})')

        if proc.returncode:
            return proc.returncode

    return 0


def run():  # pragma: no cover
    try:
        args = parse_args()
    except ValueError as e:
        print(f'{type(e).__name__}: {e}', file=sys.stderr)
        return 1

    scripts = get_scripts(args)

    print('Will run:')
    for script in scripts:
        print(f'* {shlex.join(script)}')
    if not args.confirm and input("Type 'Y' to confirm: ").upper() != 'Y':
        return 1

    if not args.nolog:
        print('Logging start...')
        log(f'Starting import for {args.wiki} (XML: {args.xml}; Images: {args.images}) (START)')

    return_code = run_scripts(args, scripts)

    if not args.nolog:
        print('Logging end...')
        log(f'Finished import for {args.wiki} (XML: {args.xml}; Images: {args.images}) (END - exit={return_code})')

    return return_code


if __name__ == '__main__':  # pragma: no cover
    sys.exit(run())
