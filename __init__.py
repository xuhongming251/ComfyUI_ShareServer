# web extension dir
# dir of share_server_extention.js
WEB_DIRECTORY = "."

from aiohttp import web
from server import PromptServer
import os
import json

from .process_manager import get_shared_url_by_start_turn_process, stop_turn_server_process

# extend custom server api for menu "Start Share My ComfyUI Server" click
@PromptServer.instance.routes.post("/start_share_server")
async def start_share_server(request):


    current_dir = os.path.abspath(os.path.dirname(__file__))
    
    proxy_config_path = os.path.join(current_dir, "proxy_config.json")

    proxy = ""

    try:

        with open(proxy_config_path, 'r') as file:
            data = json.load(file)
            proxy = data["proxy"]
            print(f"start share server by proxy: {proxy},  by config path: {proxy_config_path}")
    except:
        print(f"start share server by proxy, parse proxy config file failed!!!, {proxy_config_path}")

    os.environ['http_proxy'] = proxy
    os.environ['https_proxy'] = proxy
    
    data = await request.json()
    
    port = data.get("port")
    
    print("port: ", port)
    
    try:
        address = get_shared_url_by_start_turn_process(port)
    except Exception as e:
        print(f"start turn server, exception: {e}")
        
        return web.json_response(f"failed to start. {e}")
    
    return web.json_response(address)

# extend custom server api for menu "Stop Share My ComfyUI Server" click
@PromptServer.instance.routes.post("/stop_share_server")
async def start_share_server(request):

    result = stop_turn_server_process()
    
    if result:
        return web.json_response("Stoped")
    else:
        return web.json_response("Have Stoped")


# have none custom nodes
NODE_CLASS_MAPPINGS = {
}

NODE_DISPLAY_NAME_MAPPINGS = {
}

