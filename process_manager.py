

import os
import sys
import subprocess
import platform
import time
from multiprocessing import shared_memory
import psutil



def is_windows():
    return platform.system() == 'Windows'

global_process = None

def get_shared_url_by_start_turn_process(port):
    if is_windows():
        return get_shared_url_by_start_turn_process_win(port)
    else:
        return get_shared_url_by_start_turn_process_linux(port)

def stop_turn_server_process():
    if is_windows():
        return stop_turn_server_process_win()
    else:
        return stop_turn_server_process_linux()

def start_child_process_win(py_module_abs_path, args_params = []):
    args = [sys.executable, py_module_abs_path]
    args = args + args_params
    # print(args)
    return subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # text=True
    )

def get_shared_url_by_start_turn_process_win(port):
    global global_process
    if global_process:
        stop_turn_server_process_linux()
        global_process = None

    current_dir = os.path.abspath(os.path.dirname(__file__))
    
    get_turn_url_process_py_path = os.path.join(current_dir, "get_turn_url_process.py")

    proxy_config_path = os.path.join(current_dir, "proxy_config.json")

    shm = shared_memory.SharedMemory(create=True, size=1024)

    print("share server begin start.")
    process = start_child_process_win(get_turn_url_process_py_path, [shm.name, str(port)])
    
    address = ''

    print("share server process started, begin wait for recv message from turn server.")

    sleep_count = 0
    success = False

    while True:
        size = int.from_bytes(shm.buf[:4], 'little')
        
        if size > 0:
            byte_data = bytes(shm.buf[4:4+size])
            data = byte_data.decode('utf-8')
            print("message from trun server process:", data)
            address = data
            success = True
            break

        time.sleep(1)
        sleep_count = sleep_count + 1
        if sleep_count > 10:
            print( f'Failed, timeout! Make sure your env can access "https://api.gradio.app/" \n\nYou can try to set proxy by config file:\n\n{proxy_config_path}')
            address = f'Failed, timeout! Make sure your env can access "https://api.gradio.app/" \n\nYou can try to set proxy by config file:\n\n{proxy_config_path}'
            success = False
            stop_turn_server_process_win()
            break

    if success:
        global_process = process
    return address



def get_shared_url_by_start_turn_process_linux(port):
    
    global global_process
    
    if global_process:
        stop_turn_server_process_linux()
        global_process = None
    
    parent_conn, child_conn = os.pipe()
    
    current_dir = os.path.abspath(os.path.dirname(__file__))
    
    get_turn_url_process_py_path = os.path.join(current_dir, "get_turn_url_process.py")
    
    process = subprocess.Popen(
        [sys.executable, get_turn_url_process_py_path, str(child_conn), str(port)],
        pass_fds=(child_conn,)
    )
    print("have started")

    os.close(child_conn)

    address = ''
    with os.fdopen(parent_conn) as pipe:
        address = pipe.read()
        print("got address in main", address)
    
    global_process = process

    return address

def stop_turn_server_process_linux():
    global global_process
    
    if global_process:
        global_process.terminate()
        global_process.wait()
        global_process = None
        print("turn server stopped")
        return True
    else:
        print("no turn server to stop")
        return False
    

def kill_proc_tree(pid, including_parent=True): 
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.terminate()
        psutil.wait_procs(children, timeout=5)
        if including_parent:
            parent.terminate()
            parent.wait(5)
    except psutil.NoSuchProcess:
        pass    

def stop_turn_server_process_win():
    global global_process
    
    if global_process:
        # global_process.terminate()
        # global_process.wait()
        kill_proc_tree(global_process.pid)
        global_process = None
        print("turn server stopped")
        return True
    else:
        print("no turn server to stop")
        return False

if __name__ == "__main__":
    address = get_shared_url_by_start_turn_process_win(8199)
    print("return address ", address)
    stop_turn_server_process_win()

