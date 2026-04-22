import psutil
from block_structure.config import BLOCK_APPS

def kill_apps():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] in BLOCK_APPS:
            try:
                proc.kill()
            except:
                pass