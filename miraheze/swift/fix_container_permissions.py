import argparse
import re
import subprocess


def run_mwscript_setcontainersaccess(wiki: str, check: bool) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ['mwscript', 'CreateWiki:SetContainersAccess', wiki],
        capture_output=True,
        text=True,
        check=check
    )


def fix_container_perms(wiki: str) -> None:
    out = run_mwscript_setcontainersaccess(wiki, check=False)
    matches = re.findall(
        r"Making sure 'mwstore:\/\/miraheze-swift\/([^']+)' exists\.\.\.[^\n]*failed\.",
        (out.stdout or '') + '\n' + (out.stderr or '')
    )

    for container in matches:
        subprocess.run(
            [
                'swift',
                'post',
                '--read-acl', 'mw:media',
                '--write-acl', 'mw:media',
                f'miraheze-{wiki}-{container}',
            ],
            check=True
        )

    run_mwscript_setcontainersaccess(wiki, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description='Fix container permissions for a specified wiki')
    parser.add_argument('--wiki', required=True, help='wiki database name')

    args = parser.parse_args()
    fix_container_perms(args.wiki)


if __name__ == '__main__':
    main()
