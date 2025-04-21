from enum import Enum
import logging
import os
import platform
from string import Template
import sys
from urllib import request



# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Contants
APP_NAME = "simplex-chat"

class OS(Enum):
    LINUX = "ubuntu-22_04-x86-64"
    MACOS = "macos-x86-64"
    WINDOWS = "windows-x86-64"



class DownloadSimpleX:
    """Automatic download of simplex client from the offical simplex github page

    The download will be saved to the current working directory if the client is already download
    it will be run in the background.
    """
    
    def __init__(self):
        self.base_url = Template("https://github.com/simplex-chat/simplex-chat/releases/latest/download/simplex-chat-${os}")
        self.operating_system = platform.uname().system
        self.set_platform()


    def set_platform(self):
        if self.operating_system == "Windows":
            self.operating_system = OS.WINDOWS.value
        elif self.operating_system == "Darwin":
            self.operating_system = OS.MACOS.value
        else:
            self.operating_system = OS.LINUX.value

        
    def download(self):
        logging.info(f"Download Started")
        try:
            response = request.urlretrieve(self.base_url.safe_substitute(os=self.operating_system), APP_NAME)
            logging.info(f"Download Successful! Downloaded SimpleX for {self.operating_system} {response} ")
        except Exception as e:
            logging.info(f"Download Failed!\nError:{e}")
            sys.exit()
       
        
    
download = DownloadSimpleX()
download.download()
