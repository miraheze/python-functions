import argparse
import sys
import os
from miraheze.salt.utils import generate_salt_command, execute_salt_command, get_db_cluster


def reset_wiki(wiki: str) -> None:
    # Step 1: Get the db cluster for the wiki

    try:
        wiki_cluster = get_db_cluster(wiki)
    except (KeyError, IndexError):
        print(f'Error: Unable to determine the db cluster for {wiki}')
        sys.exit(1)

    # Step 2: Execute DeleteWiki
    execute_salt_command(salt_command=generate_salt_command('mwtask181', f'mwscript CreateWiki:DeleteWiki loginwiki --deletewiki {wiki} --delete {os.getlogin()}'))

    # Step 3: Backup and drop database
    execute_salt_command(salt_command=generate_salt_command(wiki_cluster, f"sudo -i mysqldump {wiki} > {wiki}.sql'"))
    execute_salt_command(salt_command=generate_salt_command(wiki_cluster, f"sudo -i mysql -e 'DROP DATABASE {wiki}'"))


def main() -> None:
    parser = argparse.ArgumentParser(description='Executes the commands needed to reset wikis')
    parser.add_argument('--wiki', required=True, help='Old wiki database name')

    args = parser.parse_args()
    reset_wiki(args.wiki)


if __name__ == '__main__':
    main()
