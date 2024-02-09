import os
import re
import subprocess
import sys

if len(sys.argv) != 2:
    print("Please use in form of 'python fix_containers.py foowiki'")
    sys.exit(1)

wiki = sys.argv[1]

out = subprocess.run(['sudo', '-u', 'www-data', 'php', '/srv/mediawiki/1.41/maintenance/run.php', '/srv/mediawiki/1.41/extensions/CreateWiki/maintenance/setContainersAccess.php', '--wiki', wiki], capture_output=True, text=True)

matches = re.findall(r"Making sure 'mwstore:\/\/miraheze-swift\/([^']+)' [^\n]+\.failed\.", out.stdout)
for match in matches:
    os.system(f"swift post --read-acl 'mw:media' --write-acl 'mw:media' miraheze-{wiki}-{match}")

os.system(f'sudo -u www-data php /srv/mediawiki/1.41/maintenance/run.php /srv/mediawiki/1.41/extensions/CreateWiki/maintenance/setContainersAccess.php --wiki {wiki}')
