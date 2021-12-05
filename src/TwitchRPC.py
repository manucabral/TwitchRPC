from subprocess import check_output
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
VERSION = "0.0.3"

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
    def __init__(self, name, full_name, process_name, local_path):
        self.name = name
        self.full_name = full_name
        self.process_name = process_name
        self.path = getenv("LOCALAPPDATA") + local_path
        self.db_file = "\\History"

    def running(self):
        output = check_output(
            f'wmic process where "name=\'{self.process_name}\'" get ExecutablePath', universal_newlines=True, stderr=subprocess.PIPE)
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
        return self.execute_query(path, f"SELECT title, url from urls ORDER BY last_visit_time DESC limit 1")[0]


class TwitchRPC:
    def __init__(self, client_id):
        self.client_id = client_id
        self.browser = Browser("Yandex", "Yandex Browser", "browser.exe",
                               "\\Yandex\\YandexBrowser\\User Data\\Default")
        self.rpc = None
        self.running = False

    def init_settings(self):
        system(f'title {APP_FULLNAME}')

    def is_twitch(self, title, url):
        return True if "twitch" in title.lower() and "twitch" in url.lower() else False

    def main_event(self):
        previous_streamer = None
        while self.running:
            title, url = self.browser.current_website()
            streamer = title.split(" ")[0]
            if self.is_twitch(title, url):
                if streamer != previous_streamer:
                    start_time = time()
                    previous_streamer = streamer
                self.rpc.update(details='Watching ' +
                                title.split(" ")[0], start=start_time)
            else:
                self.rpc.update(details='Offline')
            sleep(15)

    def connect_rpc(self):
        try:
            self.rpc = Presence(self.client_id, pipe=0)
            self.rpc.connect()
        except exceptions.DiscordNotFound:
            print(f'{Fore.RED}Discord is not running{Fore.RESET}')
            system('pause > nul')
            sys.exit()

        except Exception as e:
            print(f'An error occurred {e}')
        print(f'{Fore.GREEN}Successfully connected{Fore.RESET}')

    def run(self):
        if not self.running:
            init()
            self.init_settings()
            print(BANNER)

        self.connect_rpc()
        self.running = True

        try:
            self.main_event()
        except KeyboardInterrupt:
            self.rpc.close()
        except exceptions.InvalidID:
            print(
                f"{Fore.LIGHTRED_EX}Connection lost, reconnecting..{Fore.RESET}")
            sleep(10)
            self.run()


if __name__ == '__main__':
    client = TwitchRPC(":D")
    client.run()
