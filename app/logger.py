

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    END = '\033[0m'


def log_info(message):
    print(f'{Colors.GREEN}[INFO]{Colors.END} {message}')

def log_warning(message):
    print(f'{Colors.YELLOW}[WARNING]{Colors.END} {message}')

def log_error(message):
    print(f'{Colors.RED}[ERROR]{Colors.END} {message}')