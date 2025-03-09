import subprocess
import sys
from typing import Optional, TypedDict


class DbClusterMap(TypedDict):
    c1: str
    c2: str
    c3: str
    c4: str


# Define the mapping of db clusters to db names
db_clusters: DbClusterMap = {
    'c1': 'db151',
    'c2': 'db161',
    'c3': 'db171',
    'c4': 'db181',
}


def generate_salt_command(cluster: str, command: str) -> str:
    return f'salt-ssh -E "{cluster}" cmd.run "{command}"'


def execute_salt_command(salt_command: str, shell: bool = True, stdout: Optional[int] = None, text: Optional[bool] = None) -> Optional[subprocess.CompletedProcess]:
    response = input(f'EXECUTE (type c(continue), s(kip), a(bort): {salt_command}')
    if response in ['c', 'continue']:
        try:
            return subprocess.run(salt_command, shell=shell, stdout=stdout, text=text, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Command '{salt_command}' failed with return code {e.returncode}")
        except Exception as e:
            print(f'An error occurred: {e}')
        return None
    if response in ['s', 'skip']:
        return None
    sys.exit(1)  # noqa: R503


def get_db_cluster(wiki: str) -> str:
    db_query = f"SELECT wiki_dbcluster FROM mhglobal.cw_wikis WHERE wiki_dbname = '{wiki}'"
    command = generate_salt_command('db171', f"sudo -i mysql --skip-column-names -e '{db_query}'")
    result = execute_salt_command(salt_command=command, stdout=subprocess.PIPE, text=True)
    if result:
        cluster_name = result.stdout.strip()
        cluster_data = cluster_name.split('\n')
        cluster_data_b = cluster_data[1].split(' ')
        print(cluster_data_b)
        cluster_name = cluster_data_b[4]

        return db_clusters[cluster_name]  # type: ignore[literal-required]
    raise KeyboardInterrupt('Impossible to skip. Aborted.')
