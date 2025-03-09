import re
import subprocess
import argparse


def fix_container_perms(wiki: str) -> None:
    out = subprocess.run(['sudo', '-u', 'www-data', 'php', '/srv/mediawiki/1.43/maintenance/run.php', 'CreateWiki:SetContainersAccess', '--wiki', wiki], capture_output=True, text=True)
    matches = re.findall(r"Making sure 'mwstore:\/\/miraheze-swift\/([^']+)' [^\n]+\.failed\.", out.stdout)
    for match in matches:
        subprocess.run(['swift', 'post', '--read-acl', 'mw:media', '--write-acl', 'mw:media', f'miraheze-{wiki}-{match}'], check=True)

    subprocess.run(['sudo', '-u', 'www-data', 'php', '/srv/mediawiki/1.43/maintenance/run.php', 'CreateWiki:SetContainersAccess', '--wiki', wiki])


def main() -> None:
    parser = argparse.ArgumentParser(description='Fix container permissions for a specified wiki')
    parser.add_argument('--wiki', required=True, help='wiki database name')

    args = parser.parse_args()
    fix_container_perms(args.wiki)


if __name__ == '__main__':
    main()
