from enum import Enum
import logging
import os
from string import Template
import subprocess
from urllib import request



# Configure logging
logging.basicConfig(format="[%(levelname)s] [%(message)s]",level=logging.INFO)
logger = logging.getLogger(__name__)


# Contants
APP_NAME:str = "simplex-chat"



class OS(Enum):
    LINUX = "ubuntu-22_04-x86-64"
    MACOS = "macos-x86-64"
    WINDOWS = "windows-x86-64"



class SimpleXDaemon:
    """Automatic download of simplex client from the offical simplex github page

    The download will be saved to the current working directory if the client is already download
    it will be run in the background.
    """
    
    def __init__(self):
        self.base_url = Template("https://github.com/simplex-chat/simplex-chat/releases/latest/download/simplex-chat-${os}")
        self.cwd = os.getcwd()
        self.operating_system = os.uname().sysname
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
            os.chmod(f"{self.cwd}/{APP_NAME}", 0o755)
            logging.info(f"Download Successful! Downloaded SimpleX for {self.operating_system}")
        except Exception as e:
            logging.info(f"Download Failed!\nError:{e}")
            sys.exit(1)



    def run(self):
        cwd_dir = os.listdir(self.cwd)
        if APP_NAME in cwd_dir:
            print("Downloaded")
            subprocess.Popen([f"{self.cwd}/{APP_NAME}","--chat-server-port","5225", "--mute"])
        else:
            self.download()
            self.run()
        


