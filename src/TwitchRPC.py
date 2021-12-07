from subprocess import check_output, PIPE
from pypresence import Presence, exceptions
from time import time, sleep
from colorama import init, Fore
from os import system
from sys import exit
from requests import get
from json import loads

NAME = "Twitch Rich Presence"
AUTHOR = "ne0de"
VERSION = "0.5"

BANNER = f'''
{Fore.LIGHTMAGENTA_EX} 
████████╗██╗    ██╗██╗████████╗ ██████╗██╗  ██╗██████╗ ██████╗  ██████╗
╚══██╔══╝██║    ██║██║╚══██╔══╝██╔════╝██║  ██║██╔══██╗██╔══██╗██╔════╝
   ██║   ██║ █╗ ██║██║   ██║   ██║     ███████║██████╔╝██████╔╝██║     
   ██║   ██║███╗██║██║   ██║   ██║     ██╔══██║██╔══██╗██╔═══╝ ██║     
   ██║   ╚███╔███╔╝██║   ██║   ╚██████╗██║  ██║██║  ██║██║     ╚██████╗
   ╚═╝    ╚══╝╚══╝ ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝      ╚═════╝
{Fore.RESET}

{Fore.LIGHTWHITE_EX}Version: {Fore.YELLOW}{VERSION}{Fore.RESET}
{Fore.LIGHTWHITE_EX}Author: {Fore.YELLOW}{AUTHOR}{Fore.RESET}

Press {Fore.YELLOW}CTRL + C {Fore.RESET}to exit
'''

BROWSERS = [
    ('Yandex', 'Yandex Browser', 'browser.exe'),
    ('Chrome', 'Google Chrome', 'chrome.exe'),
    ('Edge', 'Microsoft Edge', 'msedge.exe'),
    ('Brave', 'Brave', 'brave.exe'),
    ('Opera', 'Opera', 'opera.exe'),
    ('Vivaldi', 'Vivaldi', 'vivaldi.exe'),
    ('Firefox', 'Mozilla Firefox', 'firefox.exe')
]

TOKENS = [
    ('Following',
     'Live Channels',
     'Latest Videos',
     'Hosts You Follow',
     'Categories',
     'All Channels You Follow',
     'Categories',
     'Top Channels')
]


class Browser:
    def __init__(self, args):
        self.name = args[0]
        self.full_name = args[1]
        self.process_name = args[2]

    def running(self):
        return True if self.name.lower() in check_output(f'wmic process where "name=\'{self.process_name}\'" get ExecutablePath', universal_newlines=True, stderr=PIPE).lower() else False

    def current_website(self):
        token = "- Twitch"
        title = check_output(f'tasklist.exe /fi "imagename eq {self.process_name}" /fo list /v | find "Window Title:"', shell=True, universal_newlines=True, stderr=PIPE).split('\n')[0]
        return title[14:] if token in check_output(f'tasklist.exe /fi "imagename eq {self.process_name}" /fo list /v | find "Window Title:"', shell=True, universal_newlines=True, stderr=PIPE).split('\n')[0] else False

class TwitchRPC:
    def __init__(self, client_id):
        self.client_id = client_id
        self.browser = self.rpc = self.running = self.prev_streamer = self.start_time = None

    def init_settngs(self):
        init()
        system('title ' + NAME)
        print(BANNER)

    def message(self, color, msg):
        print(color + msg + Fore.RESET)

    def check_update(self):
        data = get("https://api.github.com/repos/manucabral/TwitchRPC/releases").json()
        versions = []
        for key in data:
            versions.append(key['tag_name'])
        if versions[0] != VERSION:
            self.message(Fore.LIGHTYELLOW_EX, f'New update is available > {versions[0]}, please update.')
        else:
            self.message(Fore.GREEN, "Up to date")


    def get_url(self, title):
        return "https://www.twitch.tv/" + title.split(' ')[0]

    def get_browsers(self):
        browsers = []
        for browser in BROWSERS:
            output = check_output(f'wmic process where "name=\'{browser[2]}\'" get ExecutablePath', universal_newlines=True, stderr=PIPE)
            browsers.append(browser) if browser[0].lower() in output.lower() else None
        return browsers

    def select_browser(self, max):
        while True:
            try:
                option = int(input(f'\nSelect a browser to continue: '))
                if 0 <= option < max:
                    return option
            except (ValueError, TypeError):
                self.message(Fore.RED, 'Please pick a number')

    def browser_handler(self, browsers):
        if len(browsers) == 0:
            self.message(Fore.LIGHTRED_EX, 'Could not locate a running browser')
            self.stop()

        if len(browsers) == 1:
            browser = browsers[0]
            self.message(Fore.GREEN, f'Found {browser[1]}!')
            self.browser = Browser(browser)

        if len(browsers) > 1:
            self.message(Fore.LIGHTCYAN_EX, f'Currently {len(browsers)} browsers running..')
            for i, browser in enumerate(browsers):
                self.message( Fore.WHITE, f'{Fore.CYAN}[{i}]{Fore.RESET} {browser[1]}')
            option = self.select_browser(len(browsers))
            self.message(Fore.CYAN, f'You selected: {browsers[option][1]}')
            self.browser = Browser(browsers[option])

    def connect_rpc(self):
        try:
            self.rpc = Presence(self.client_id, pipe=0)
            self.rpc.connect()
        except exceptions.DiscordNotFound:
            self.message(Fore.LIGHTRED_EX, 'Discord is not running')
            self.stop()
        except Exception as e:
            self.message(Fore.RED, e)
        self.message(Fore.LIGHTGREEN_EX, 'Successfully connected')

    def get_token(self, title):
        for token in TOKENS[0]:
            if token in title:
                return 'Browsing in ' + token
        return None

    def twitch_handler(self, title):
        img = "logo"
        start_time = button = None
        details = self.get_token(title)
        if not details:
            streamer = title.split(" ")[0]
            details = 'Watching ' + streamer
            button = [{"label": "Go to stream", "url": self.get_url(title)}]
            if streamer != self.prev_streamer:
                self.start_time = time()
                self.prev_streamer = streamer
        return {
            'details': details,
            'start': self.start_time,
            'large_image': img,
            'buttons': button
        }

    def update_presence(self):
        title = self.browser.current_website()
        data = None
        if not title:
            self.rpc.update(details="Offline", large_image='logo')
        else:
            data = self.twitch_handler(title)
            self.rpc.update(**data)

    def main_event(self):
        while self.running:
            if self.browser.running():
                self.update_presence()
            else:
                self.message(Fore.CYAN, f'Could not locate {self.browser.name} process')
                self.running = False
                self.run()
            sleep(15)

    def stop(self):
        self.running = False
        system('pause > nul')
        exit()

    def run(self):
        system('cls')
        if not self.running:
            self.init_settngs()
            self.message(Fore.YELLOW, 'Checking updates..')
            self.check_update()
            self.message(Fore.YELLOW, 'Scanning browsers on your system..')
            self.browser_handler(self.get_browsers())

        self.connect_rpc()
        self.running = True
        try:
            self.main_event()
        except KeyboardInterrupt:
            self.rpc.close()
        except exceptions.InvalidID:
            self.message(Fore.LIGHTRED_EX, 'Connection lost, re-connecting in 5 seconds..')
            sleep(5)
            self.run()
