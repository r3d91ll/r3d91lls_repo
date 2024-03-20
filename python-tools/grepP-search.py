import os
import re
import logging
import subprocess
import multiprocessing
import tracemalloc
import signal
import sys
from multiprocessing import Lock

LOG_FILE = "/root/grep_search_log_file.txt"
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])

SEARCH_DIR = "/"
OUTPUT_FILE = "/root/grep_search_output_file.txt"
SCRIPT_FILE = "/root/your_script.py"
EXCLUDE_DIRS = ['/proc', '/sys', '/dev', '/root', OUTPUT_FILE, SCRIPT_FILE]
PATTERN = re.compile(r"grep\s+(?:-[a-zA-Z]*\s)*-P\s+'.+'")

file_lock = Lock()

def is_text_file(file_path):
    try:
        file_lock.acquire(timeout=5)
        try:
            output = subprocess.check_output(['file', '--brief', '--mime-type', file_path], timeout=5)
            return output.decode().strip().startswith('text/')
        finally:
            file_lock.release()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, multiprocessing.TimeoutError):
        return False
    except KeyboardInterrupt:
        print("File check interrupted by user.")
        return False

def search_file(file_path):
    if not is_text_file(file_path):
        return None

    line_numbers = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            for line_no, line in enumerate(file, 1):
                if PATTERN.search(line):
                    line_numbers.append(str(line_no))
    except PermissionError:
        logging.warning('Permission denied to read file: %s', file_path)
    except UnicodeDecodeError:
        logging.warning('Unable to decode file: %s', file_path)
    except Exception as e:
        logging.error('Error reading file %s: %s', file_path, e)

    if line_numbers:
        return f"{file_path}:{','.join(line_numbers)}"
    return None

def should_ignore_path(path):
    return any(path.startswith(ignore) for ignore in EXCLUDE_DIRS)

def find_files(directory):
    for root, _, files in os.walk(directory):
        if should_ignore_path(root):
            continue
        for file in files:
            file_path = os.path.join(root, file)
            if not should_ignore_path(file_path):
                yield file_path

def signal_handler(signal, frame):
    print("Script interrupted by user.")
    sys.exit(0)

def main():
    tracemalloc.start()

    cpu_count = os.cpu_count() or 1
    pool = multiprocessing.Pool(processes=cpu_count)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        results = pool.map(search_file, find_files(SEARCH_DIR))
        with open(OUTPUT_FILE, 'w') as output_file:
            for result in filter(None, results):
                output_file.write(f"{result}\n")
    except KeyboardInterrupt:
        print("Script interrupted by user.")
        pool.terminate()  # Terminate worker processes
        pool.join()  # Wait for worker processes to finish
    finally:
        pool.close()
        pool.join()

    current, peak = tracemalloc.get_traced_memory()
    logging.debug('Current memory usage: %d KB, Peak memory usage: %d KB', current / 1024, peak / 1024)

    tracemalloc.stop()
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Script interrupted by user.")