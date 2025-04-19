from enum import Enum
import logging
import platform
from string import Template
import urllib



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
        self.os = platform.uname().system
        self.set_platform()


    def set_platform(self):
        if self.os == "Windows":
            self.os = OS.WINDOWS.value
        elif self.os == "Darwin":
            self.os = OS.MACOS.value
        else:
            self.os = OS.LINUX.value

        
    def download(self):
        logging.info(f"Starting download simplex for {self.os}")
        try:
            response = urllib.request.urlretrieve(self.base_url.safe_substitute(os=self.os), APP_NAME)
        except Exception as e:
            logging.info(f"""Download Failed!
Error:{e}""")
       
        
        
        
down = DownloadSimpleX()

down.download()
