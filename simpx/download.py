from enum import Enum
import platform
from string import Template



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
        self.base_link = Template("https://github.com/simplex-chat/simplex-chat/releases/latest/download/simplex-chat-${os}")
        self.os = platform.uname().system
        self.set_platform()


    def set_platform(self):
        if self.os == "Linux":
            self.os = OS.LINUX.value
        elif self.os == "Darwin":
            self.os = OS.MACOS.value
        else:
            self.os = OS.WINDOWS.value

        
    def download(self):
        pass
