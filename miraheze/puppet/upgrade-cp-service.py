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
HOSTNAME = socket.gethostname().partition('.')[0]

class ServersAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):  # noqa: U100
        """
        Parse and validate server choices from a comma-separated input string.
        
        Splits the input into individual server names and verifies each against the current
        environment's valid servers. If the keyword "all" is present, it replaces the list with
        all available servers. Triggers a parser error if any invalid server names are found.
        """
        input_servers = values.split(',')
        valid_servers = get_environment_info()['servers']
        if 'all' in input_servers:
            input_servers = valid_servers
        invalid_servers = set(input_servers) - set(valid_servers)
        if invalid_servers:
            parser.error(f'invalid server choice(s): {", ".join(invalid_servers)}')
        setattr(namespace, self.dest, input_servers)

def run_command(command):
    """
    Executes a shell command and returns its output.
    
    This function runs the given command in a subshell using the subprocess module.
    It captures the command's standard output and returns it after stripping any
    extraneous whitespace. If the command fails, it prints an error message and
    returns None.
    
    Args:
        command (str): The shell command to execute.
    
    Returns:
        str or None: The command's output if successful; otherwise, None.
    """
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing {command}: {e}")
        return None

def wait_for_ping(server, timeout=300, interval=5):
    """
    Waits for a server to become reachable via ping.
    
    Repeatedly pings the specified server at regular intervals until it responds or the timeout is reached.
    Prints status messages indicating whether the server has come back online, and returns a boolean
    value signifying the server's availability.
    
    Args:
        server: The address or hostname of the server to ping.
        timeout: The maximum time in seconds to wait for a response (default is 300).
        interval: The interval in seconds between consecutive ping attempts (default is 5).
    
    Returns:
        True if the server responds within the timeout period, otherwise False.
    """
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
    """
    Checks whether the target service is operational by querying its MediaWiki API.
    
    This function sends a GET request over HTTPS to the API endpoint at the given domain.
    If a debug identifier is provided, it attaches custom headers and verifies that the
    response header includes the expected debug context. The service is considered up if the
    response has a 200 status code, contains the 'miraheze' marker in its body, and, when
    debugging is active, the debug identifier is present in the 'X-Served-By' header.
    SSL verification is controlled by the verify flag (with warnings suppressed when disabled).
    Diagnostic messages are printed if the service does not meet these checks.
    
    Parameters:
        Debug: A debug identifier used to insert and validate custom headers.
        domain: The service domain to query (default "meta.miraheze.org").
        verify: Flag to enforce SSL certificate verification (default True).
    
    Returns:
        True if the service is healthy; otherwise, False.
    """
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
    """
    Processes the upgrade workflow for the specified server.
    
    This function orchestrates the server upgrade steps by marking the backend as sick,
    upgrading packages, rebooting the server, and then verifying that the server is back online.
    If the server responds to a ping, it conducts a health check and, if successful, restores
    the backend health to auto. If the health check fails or the server does not respond to ping,
    the function pauses until the user confirms to continue.
    
    Parameters:
        server: The hostname or identifier of the server to process.
    """
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
    for server in args.servers:
        process_server(args.servers)
