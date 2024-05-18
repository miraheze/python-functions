import os
import re
import subprocess
import argparse


def fix_container_perms(wiki: str) -> None:
    out = subprocess.run(['sudo', '-u', 'www-data', 'php', '/srv/mediawiki/1.41/maintenance/run.php', '/srv/mediawiki/1.41/extensions/CreateWiki/maintenance/setContainersAccess.php', '--wiki', wiki], capture_output=True, text=True)
    matches = re.findall(r"Making sure 'mwstore:\/\/miraheze-swift\/([^']+)' [^\n]+\.failed\.", out.stdout)
    for match in matches:
        os.system(f"swift post --read-acl 'mw:media' --write-acl 'mw:media' miraheze-{wiki}-{match}")

    os.system(f'sudo -u www-data php /srv/mediawiki/1.41/maintenance/run.php /srv/mediawiki/1.41/extensions/CreateWiki/maintenance/setContainersAccess.php --wiki {wiki}')


def main() -> None:
    parser = argparse.ArgumentParser(description='Executes the commands needed to reset wikis')
    parser.add_argument('--wiki', required=True, help='wiki database name')

    args = parser.parse_args()
    fix_container_perms(args.wiki)


if __name__ == '__main__':
    main()
