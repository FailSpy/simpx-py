import hashlib
import logging
import os
import subprocess
import shutil

from enum import Enum
from string import Template
from pathlib import Path


import requests
from tqdm import tqdm
from requests.exceptions import ConnectionError, Timeout



# Configure logging
logging.basicConfig(format="[%(levelname)s] %(message)s",level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Contants
APP_NAME:str = "simplex-chat"
DIR_NAME:str = "simplex-dir"
download_dir:str = os.path.join(Path.home(),DIR_NAME)
abs_file_path:str = os.path.join(download_dir,APP_NAME)
# 
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
        # Link used to check hashes
        self.release_url = "https://github.com/simplex-chat/simplex-chat/releases"
        self.operating_system = os.uname().sysname
        self.set_platform()

    # The OS will default to linux version 
    def set_platform(self):
        if self.operating_system == "Windows":
            self.operating_system = OS.WINDOWS.value
            APP_NAME = APP_NAME+".exe"
        elif self.operating_system == "Darwin":
            self.operating_system = OS.MACOS.value
        else:
            self.operating_system = OS.LINUX.value

        
    def download(self):
        logging.info(f"Download Started")
        try:
            response = requests.get(url=self.base_url.safe_substitute(os=self.operating_system), stream=True)
            total_size = int(response.headers.get('content-length', 0))
            with open(abs_file_path, 'wb') as file, tqdm(
                desc=f"Downloading SimpleX for \033[5m {self.operating_system} \033[0m",
                total=total_size,
                unit='iB',
                unit_scale=True
            )as progress_bar:
                    for data in response.iter_content(chunk_size=1024):
                        size = file.write(data)
                        progress_bar.update(size)
                
            
            # Will add integrity checks here
            # Until simplex hash contains all the hashes need to verify install this will be the default
            with open(abs_file_path,"rb") as file:
                digest = hashlib.file_digest(file, "sha256").hexdigest()
            logging.info(f"SimpleX file hash: \033[1m {digest} \033[0m")
            logging.info(f"Chech hash here: {self.release_url}")

            while True:
                file_integrity_check = input("Is the hash correct?[y,N] ")
                if file_integrity_check.lower() in ['', 'y', "yes"]:
                    os.chmod(abs_file_path, 0o755)
                    logging.info(f"Download Successful!")
                    # Simplex needs to be run so that there is an initial user
                    # proccess dies after 50 secs
                    subprocess.run([abs_file_path])
                    break
                elif file_integrity_check.lower() in ['n',"no"]:
                    logging.info("Retrying download!")
                    self.download()
                    break
                else:
                    logging.warning("Input not recognized.")
                    continue
                
        except ConnectionError:
            logging.critical(f"Connection Failed! Are you connected to the internet?")
            os.sys.exit(1)
        except Timeout:
            logging.critical(f"Connection timed out.")
            shutil.rmtree(download_dir)
            os.sys.exit(1)
        except KeyboardInterrupt:
            logging.info("Exiting")
            os.sys.exit(1)
        except Exception as e:
            logging.critical(f"Download Failed!\nError: {e}")
            shutil.rmtree(download_dir)
            os.sys.exit(1)


    def run(self, port_number=5225):
        try:
            if APP_NAME in os.listdir(download_dir):
                logging.info("Already downloaded.")
                bg_task = subprocess.Popen([f"{abs_file_path}","--chat-server-port",f"{port_number}", "--mute"])
            else:
                self.download()
                self.run()
        except KeyboardInterrupt:
            logging.info("Exiting")
            bg_task.kill()
        except UnboundLocalError:
            logging.warning("Background Task not running so not killed.")
        except PermissionError:
            logging.critical("Premission denied while try to access executable.")
            shutil.rmtree(abs_file_path)
        except Exception as e:
            logging.critical("Running simplex in the background failed")
            bg_task.kill() 


