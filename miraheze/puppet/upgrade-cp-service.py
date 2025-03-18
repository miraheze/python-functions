import subprocess
import time
import os

class Environment(TypedDict):
    wikidbname: str
    wikiurl: str
    servers: list


class EnvironmentList(TypedDict):
    beta: Environment
    prod: Environment


beta: Environment = {
    'wikidbname': 'metawikibeta',
    'wikiurl': 'meta.mirabeta.org',
    'servers': ['test151'],
}


prod: Environment = {
    'wikidbname': 'testwiki',
    'wikiurl': 'publictestwiki.com',
    'servers': [
        'mw151',
        'mw152',
        'mw161',
        'mw162',
        'mw171',
        'mw172',
        'mw181',
        'mw182',
        'mwtask171',
        'mwtask181',
    ],
}
ENVIRONMENTS: EnvironmentList = {
    'beta': beta,
    'prod': prod,
}
del beta
del prod
HOSTNAME = socket.gethostname().split('.')[0]

class ServersAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):  # noqa: U100
        input_servers = values.split(',')
        valid_servers = get_environment_info()['servers']
        if 'all' in input_servers:
            input_servers = valid_servers
        invalid_servers = set(input_servers) - set(valid_servers)
        if invalid_servers:
            parser.error(f'invalid server choice(s): {", ".join(invalid_servers)}')
        setattr(namespace, self.dest, input_servers)

def run_command(command):
    """Runs a shell command and returns the output."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing {command}: {e}")
        return None

def wait_for_ping(server, timeout=300, interval=5):
    """Waits for the server to respond to ping."""
    print(f"Waiting for {server} to come back online...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = os.system(f"ping -c 1 {server} > /dev/null 2>&1")
        if response == 0:
            print(f"{server} is back online!")
            return True
        time.sleep(interval)
    print(f"Timeout waiting for {server} to come back online.")
    return False

def check_up(Debug: str, domain: str = 'meta.miraheze.org', verify: bool = True) -> bool:
    if verify is False:
        os.environ['PYTHONWARNINGS'] = 'ignore:Unverified HTTPS request'

    headers = {}
    if Debug:
        server = f'{Debug}.wikitide.net'
        headers['X-WikiTide-Debug'] = server
        location = f'{domain}@{server}'

        debug_access_key = os.getenv('DEBUG_ACCESS_KEY')

        # Check if DEBUG_ACCESS_KEY is set and add it to headers
        if debug_access_key:
            headers['X-WikiTide-Debug-Access-Key'] = debug_access_key
    up = False
    req = requests.get(f'https://{domain}:{port}/w/api.php?action=query&meta=siteinfo&formatversion=2&format=json', headers=headers, verify=verify)
    if req.status_code == 200 and 'miraheze' in req.text and (Debug is None or Debug in req.headers['X-Served-By']):
        up = True
    if not up:
        print(f'Status: {req.status_code}')
        print(f'Text: {"miraheze" in req.text} \n {req.text}')
        if 'X-Served-By' not in req.headers:
            req.headers['X-Served-By'] = 'None'
        print(f'Debug: {(Debug is None or Debug in req.headers["X-Served-By"])}')
    return up

def process_server(server):
    """Performs the sequence of commands for a given server."""
    print(f"Processing {server}...")
    
    # Mark backend as sick
    run_command(f"salt-ssh -E \"cp.*\" cmd.run \"sudo varnishadm backend.set_health {server} sick\"")
    
    # Upgrade packages
    run_command(f"sudo upgrade-packages -a -s {server}")
    
    # Reboot the server
    run_command(f"sudo salt-ssh \"{server}.wikitide.net\" cmd.run 'reboot now'")
    
    # Wait for the server to come back online
    if wait_for_ping(server):
        
        # Perform health check
        if check_up(server):
            print(f"Health check passed for {server}")
            
            # Restore backend health to auto
            run_command(f"salt-ssh -E \"cp.*\" cmd.run \"sudo varnishadm backend.set_health {server} auto\"")
        else:
            print(f"Health check failed for {server}")
            input('Press enter to continue')
    else:
        print(f"Skipping health check as {server} did not respond to ping.")
        input('Press enter to continue')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--servers', dest='servers', action=ServersAction, required=True, help='server(s) to deploy to')
    args = parser.parse_args()
    for server in servers:
        process_server(args.server)
