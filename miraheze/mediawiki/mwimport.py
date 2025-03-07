#!/usr/bin/env python3
import argparse
import os
import shlex
import subprocess
import sys


def parse_args(args: list | None = None, check_paths: bool = True) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="A script to automate manual wiki imports")
    parser.add_argument(
        "--no-log", dest="nolog", action="store_true",
        help="Whether or not to disable logging to the server admin log",
    )
    parser.add_argument(
        "--confirm", "--yes", "-y", dest="confirm", action="store_true",
        help="Whether or not to skip the initial confirmation prompt",
    )
    parser.add_argument("--version", help="MediaWiki version to use (automatically detected if not passed)")
    parser.add_argument("--xml", help="XML file to import")
    parser.add_argument("--username-prefix", help="Interwiki prefix for importing XML")
    parser.add_argument("--images", help="Directory of images to import")
    parser.add_argument(
        "--images-comment", help="The comment passed to importImages.php"
        " (example: 'Importing images from https://example.com ([[phorge:T1234|T1234]])')",
    )
    parser.add_argument(
        "--search-recursively", action="store_true",
        help="Whether or not to pass --search-recursively (check files in subdirectories) to importImages.php",
    )
    parser.add_argument("wiki", help="Database name of the wiki to import to")

    args = parser.parse_args(args)
    if not args.xml and not args.images:
        raise ValueError("--xml and/or --images must be passed")
    if args.images and not args.images_comment:
        raise ValueError("--images-comment must be passed when importing images")

    # This is honestly only for unit testing as I can't really think of a reason
    # to disable this check in production
    if check_paths:
        # This is not meant to be comprehensive, but just to make sure that someone
        # doesn't typo a path or so
        if args.xml and not os.path.exists(args.xml):
            raise ValueError(f"Cannot find XML to import: {repr(args.xml)}")
        if args.images and not os.path.exists(args.images):
            raise ValueError(f"Cannot find images to import: {repr(args.images)}")

    return args


def log(message: str):
    subprocess.run(
        ["/usr/local/bin/logsalmsg", message],
        check=True,
    )


def get_version(wiki: str) -> str:
    return subprocess.run(
        ["/usr/local/bin/getMWVersion", wiki],
        stdout=subprocess.PIPE,
        check=True,
        text=True,
    ).stdout.strip()


def get_scripts(args: argparse.Namespace) -> list[list[str]]:
    scripts = []

    if args.xml:
        script = ["importDump", args.xml, "--no-updates"]
        if args.username_prefix:
            script.append(f"--username-prefix={args.username_prefix}")
        scripts.append(script)

    if args.images:
        script = ["importImages", args.images, f"--comment={args.images_comment}"]
        if args.search_recursively:
            script.append("--search-recursively")
        scripts.append(script)

    if args.xml:
        scripts.append(["rebuildall"])
        scripts.append(["initEditCount"])

    scripts.append(["initSiteStats", "--update"])

    return scripts


def run_scripts(args: argparse.Namespace, scripts: list[list[str]]) -> int:
    for script in scripts:
        print(f"Running {shlex.join(script)}")
        if not args.nolog:
            print("Logging execution...")
            log(shlex.join(script))

        proc = subprocess.run(script)

        if not args.nolog:
            print("Logging execution end...")
            log(f"{shlex.join(script)} (END - exit={proc.returncode})")

        if proc.returncode:
            return proc.returncode

    return 0


def run():
    try:
        args = parse_args()
    except ValueError as e:
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        return 1

    version = args.version or get_version(args.wiki)

    scripts = get_scripts(args)
    scripts = [
        ["sudo", "-u", "www-data", "php", f"/srv/mediawiki/{version}/maintenance/run.php", f"--wiki={args.wiki}", *script] for script in scripts
    ]

    print("Will run:")
    for script in scripts:
        print(f"* {shlex.join(script)}")
    if not args.confirm and input("Type 'Y' to confirm: ").upper() != "Y":
        return 1

    if not args.nolog:
        print("Logging start...")
        log(f"Starting import for {args.wiki} (XML: {args.xml}; Images: {args.images})")

    return_code = run_scripts(args, scripts)

    if not args.nolog:
        print("Logging end...")
        log(f"Finished import for {args.wiki} (XML: {args.xml}; Images: {args.images}) (END - exit={return_code})")

    return return_code


if __name__ == "__main__":
    sys.exit(run())
