from enum import Enum
import hashlib
import logging
import os
from string import Template
import subprocess
from pathlib import Path


import requests
from tqdm import tqdm


# Configure logging
logging.basicConfig(format="[%(levelname)s] %(message)s",level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Contants
APP_NAME:str = "simplex-chat"
DIR_NAME:str = "simplex-dir"
download_dir:str = os.path.join(Path.home(),DIR_NAME)
abs_file_path:str = os.path.join(download_dir,APP_NAME)
try:
    os.mkdir(download_dir)
except FileExistsError:
    pass



class OS(Enum):
    LINUX = "ubuntu-22_04-x86-64"
    MACOS = "macos-x86-64"
    WINDOWS = "windows-x86-64"



class SimpleXDaemon:
    """Automatic download of simplex client from the offical simplex github page

    The download will be saved to the simplex-dir folder in the /home/[user] directory if the client is already download
    it will be run in the background.
    """
    
    def __init__(self):
        self.base_url = Template("https://github.com/simplex-chat/simplex-chat/releases/latest/download/simplex-chat-${os}")
        self.operating_system = os.uname().sysname
        self.set_platform()

    # The OS will default to linux version 
    def set_platform(self):
        if self.operating_system == "Windows":
            self.operating_system = OS.WINDOWS.value
        elif self.operating_system == "Darwin":
            self.operating_system = OS.MACOS.value
        else:
            self.operating_system = OS.LINUX.value

        
    def download(self):
        logging.info(f"Download Started")
        logging.info(f"Downloading to {download_dir}")
        try:
            response = requests.get(url=self.base_url.safe_substitute(os=self.operating_system), stream=True)
            total_size = int(response.headers.get('content-length', 0))
            with open(abs_file_path, 'wb') as file, tqdm(
                desc=f"Downloading SimpleX for {self.operating_system}",
                total=total_size,
                unit='iB',
                unit_scale=True
            )as progress_bar:
                    for data in response.iter_content(chunk_size=1024):
                        size = file.write(data)
                        progress_bar.update(size)
                
            os.chmod(f"{abs_file_path}", 0o755)
            # Will add integrity checks here 
            # hashlib.sha256()
            logging.info(f"Download Successful!")
        except Exception as e:
            logging.critical(f"Download Failed!\nError:{e}")
            os.sys.exit(1)



    def run(self):
        if APP_NAME in os.listdir(download_dir):
            logging.info("Already downloaded")
            subprocess.Popen([f"{abs_file_path}","--chat-server-port","5225", "--mute"])
        else:
            self.download()
            self.run()
        


down = SimpleXDaemon()
down.run()
