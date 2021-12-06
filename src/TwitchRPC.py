from subprocess import check_output, PIPE
from sqlite3 import connect
from os import system, getenv, path
from shutil import copy2
from pypresence import Presence, exceptions
from time import time, sleep
from colorama import init, Fore
import sys

APP_NAME = "TwitchRPC"
APP_FULLNAME = "Twitch Rich Presence"
AUTHOR = "ne0de"
VERSION = "0.4"

BROWSERS = [
    ('Yandex', 'Yandex Browser', 'Chromium', 'browser.exe', '\\Yandex\\YandexBrowser\\User Data\\Default'),
    ('Chrome', 'Google Chrome', 'Chromium', 'chrome.exe', '\\Google\\Chrome\\User Data\\Default'),
    ('Edge', 'Microsoft Edge', 'Chromium', 'msedge.exe', '\\Microsoft\\Edge\\User Data\\Default')
]

BANNER = f'''
{Fore.LIGHTMAGENTA_EX} 
  ______         _ __       __    ____  ____  ______
 /_  __/      __(_) /______/ /_  / __ \/ __ \/ ____/
  / / | | /| / / / __/ ___/ __ \/ /_/ / /_/ / /     
 / /  | |/ |/ / / /_/ /__/ / / / _, _/ ____/ /___   
/_/   |__/|__/_/\__/\___/_/ /_/_/ |_/_/    \____/   
{Fore.RESET}

{Fore.LIGHTWHITE_EX}Version: {Fore.YELLOW}{VERSION}{Fore.RESET}
{Fore.LIGHTWHITE_EX}Author: {Fore.YELLOW}{AUTHOR}{Fore.RESET}

Press {Fore.YELLOW}CTRL + C {Fore.RESET}to exit
'''

class Browser:
    def __init__(self, args):
        self.name = args[0]
        self.full_name = args[1]
        self.type = args[2]
        self.process_name = args[3]
        self.path = getenv("LOCALAPPDATA") + args[4]
        self.db_file = "\\History"

    def running(self):
        output = check_output(
            f'wmic process where "name=\'{self.process_name}\'" get ExecutablePath', universal_newlines=True, stderr=PIPE)
        return True if self.name.lower() in output.lower() else False

    def update_db_file(self):
        temp_path = getenv("TEMP") + self.db_file
        original_path = self.path + self.db_file
        if path.isfile(temp_path):
            system(f'del {temp_path}')
        copy2(original_path, temp_path)
        return temp_path

    def execute_query(self, path, query):
        cur = connect(path).cursor()
        result = [a for a in cur.execute(query)]
        cur.close()
        return result

    def current_website(self):
        path = self.update_db_file()
        result = self.execute_query(path, f"SELECT title, url from urls ORDER BY last_visit_time DESC limit 1")
        return (0, 0) if not result else result[0]


class TwitchRPC:
    def __init__(self, client_id):
        self.client_id = client_id
        self.browser = None
        self.rpc = None
        self.running = False

    def message(self, color, m):
        print(color + m + Fore.RESET)

    def init_settings(self):
        system(f'title {APP_FULLNAME}')

    def is_twitch(self, title, url):
        return True if "twitch" in title.lower() and "twitch" in url.split('/')[2].lower() else False

    def detect_browsers(self):
        browsers = []
        for browser in BROWSERS:
            output = check_output(f'wmic process where "name=\'{browser[3]}\'" get ExecutablePath', universal_newlines=True, stderr=PIPE)
            browsers.append(browser) if browser[0].lower() in output.lower() else None
        return browsers

    def update_presence(self):
        title, url = self.browser.current_website()
        if title == 0:
            self.message(Fore.LIGHTRED_EX, "Can't find websites in your browser history")
            return
        streamer = title.split(" ")[0]
        previous_streamer = None
        if self.is_twitch(title, url):
            if streamer != previous_streamer:
                start_time = time()
                previous_streamer = streamer
                self.rpc.update(details='Watching ' + title.split(" ")[0], start=start_time, large_image="logo")
        else:
            self.rpc.update(details='Offline', large_image="logo")
        
    def main_event(self):
        while self.running:
            if self.browser.running():
                self.update_presence()
            else:
                self.message(Fore.CYAN, f'Could not locate {self.browser.name} process')
                self.running = False
                self.run()
            sleep(15)

    def connect_rpc(self):
        try:
            self.rpc = Presence(self.client_id, pipe=0)
            self.rpc.connect()
        except exceptions.DiscordNotFound:
            self.message(Fore.RED, 'Discord is not running')
            self.stop()
        except Exception as e:
            self.message(Fore.RED, e)
    
    def select_browser(self, max):
        while True:    
            try:
                option = int(input(f'\nSelect a browser to continue: '))
                if 0 <= option < max:
                    return option
            except (ValueError, TypeError):
                self.message(Fore.RED, 'Please pick a number')
                
    def browsers_handler(self, browsers):
        if len(browsers) == 0:
            self.message(Fore.LIGHTRED_EX, 'Could not locate a running browser')
            self.stop()
        
        if len(browsers) == 1:
            browser = browsers[0]
            self.message(Fore.GREEN, f'Found {browser[1]}!')
            self.browser = Browser(browser)
        
        if len(browsers) > 1:
            self.message(Fore.LIGHTCYAN_EX, f'Found {len(browsers)} running browsers')
            for i, browser in enumerate(browsers): self.message(Fore.WHITE, f'{Fore.CYAN}[{i}]{Fore.RESET} {browser[1]}')
            option = self.select_browser(len(browsers))
            self.message(Fore.CYAN, f'You selected: {browsers[option][1]}')
            self.browser = Browser(browsers[option])

    def stop(self):
        self.running = False
        system('pause > nul')
        sys.exit()

    def run(self):
        system('cls')

        if not self.running:
            init()
            print(BANNER)
            self.init_settings()
            self.browsers_handler(self.detect_browsers())

        self.connect_rpc()
        self.message(Fore.LIGHTGREEN_EX, 'Successfully connected')
        self.running = True

        try:
            self.main_event()
        except KeyboardInterrupt:
            self.rpc.close()
        except exceptions.InvalidID:
            self.message(Fore.LIGHTRED_EX, 'Connection lost, reconnecting..')
            sleep(10)
            self.run()

if __name__ == '__main__':
    client = TwitchRPC(":D")
    client.run()
