import argparse
import sys
from miraheze.salt.utils import generate_salt_command, execute_salt_command, get_db_cluster


def rename_wiki(oldwiki_db: str, newwiki_db: str) -> None:
    # Step 1: Get the db cluster for the old wiki dbname
    oldwiki_cluster = get_db_cluster(oldwiki_db)

    try:
        oldwiki_cluster = get_db_cluster(oldwiki_db)
    except KeyError:
        print(f'Error: Unable to determine the db cluster for {oldwiki_db}')
        sys.exit(1)

    # Step 2: Execute SQL commands for rename
    execute_salt_command(salt_command=generate_salt_command(oldwiki_cluster, f'mysqldump {oldwiki_db} > oldwikidb.sql'))
    execute_salt_command(salt_command=generate_salt_command(oldwiki_cluster, f"mysql -e 'CREATE DATABASE {newwiki_db}'"))
    execute_salt_command(salt_command=generate_salt_command(oldwiki_cluster, f"mysql -e 'USE {newwiki_db}; SOURCE /home/$user/oldwikidb.sql'"))

    # Step 3: Execute MediaWiki rename script
    execute_salt_command(salt_command=generate_salt_command('mwtask181', f'sudo -u www-data php /srv/mediawiki/1.43/maintenance/run.php CreateWiki:RenameWiki --wiki=loginwiki --rename {oldwiki_db} {newwiki_db} $user'))


def main() -> None:
    parser = argparse.ArgumentParser(description='Executes the commands needed to rename wikis')
    parser.add_argument('--oldwiki', required=True, help='Old wiki database name')
    parser.add_argument('--newwiki', required=True, help='New wiki database name')

    args = parser.parse_args()
    rename_wiki(args.oldwiki, args.newwiki)


if __name__ == '__main__':
    main()
