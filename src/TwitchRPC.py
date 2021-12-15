from requests import get, exceptions as rexceptions
from subprocess import check_output, PIPE
from pypresence import Presence, exceptions
from win10toast import ToastNotifier
from time import time, sleep
from colorama import init, Fore
from os import system
from sys import exit
from json import loads
from constants import *

class Browser:
    def __init__(self, args, lang):
        self.name = args[0]
        self.full_name = args[1]
        self.process_name = args[2]
        self.lang = lang

    def running(self):
        return True if self.name.lower() in check_output(f'wmic process where "name=\'{self.process_name}\'" get ExecutablePath', universal_newlines=True, stderr=PIPE).lower() else False

    def current_website(self):
        token = "- Twitch"
        field = "Window Title:" if "en" in self.lang else "Título de ventana:"
        title = check_output(f'tasklist.exe /fi "imagename eq {self.process_name}" /fo list /v | find "{field}"', shell=True, universal_newlines=True, stderr=PIPE).split('\n')[0]
        return title[14 if "en" in self.lang else 20:] if token in check_output(f'tasklist.exe /fi "imagename eq {self.process_name}" /fo list /v | find "{field}"', shell=True, universal_newlines=True, stderr=PIPE).split('\n')[0] else False

class TwitchRPC:
    def __init__(self, client_id):
        self.client_id = client_id
        self.toast = ToastNotifier()
        self.browser = self.rpc = self.running = self.prev_streamer = self.start_time = None
        self.lang = self.full_lang = None

    def display_logo(self):
        print(BANNER)
        self.message(Fore.WHITE, f'Version: {Fore.YELLOW}{VERSION}')
        self.message(Fore.WHITE, f'Author: {Fore.YELLOW}{AUTHOR}')
        print("")

    def init_settings(self):
        init()
        system('title ' + NAME)
        system(F'mode con:cols={COLUMNS} lines={LINES}')
        self.display_logo()

    def message(self, color, msg, toast=False, s=10):
        print(color + msg + Fore.RESET)
        try:
            if toast:
                self.toast.show_toast(NAME, msg, icon_path="assets/logo.ico", duration=s)
        except KeyboardInterrupt:
            return

    def check_update(self):
        res = get(REPO_URL)
        try:
            res.raise_for_status()
        except rexceptions.HTTPError as err:
            self.message(Fore.RED, str(err))
            return
        versions = []
        for key in res.json():
            versions.append(key['tag_name'])
        if versions[0] != VERSION:
            self.message(Fore.LIGHTYELLOW_EX, f'New update is available > {Fore.CYAN}{versions[0]}{Fore.LIGHTYELLOW_EX}, please update.')
        else:
            self.message(Fore.GREEN, "Up to date")

    def get_url(self, title):
        return TWITCH_URL + title.split(' ')[0]

    def get_streamer_bio(self, streamer):
        res = get(IVR_REPO + streamer)
        try:
            res.raise_for_status()
        except rexceptions.HTTPError as err:
            self.message(Fore.RED, str(err))
            return None
        data = res.json()
        return data['bio']

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
            except KeyboardInterrupt:
                self.stop()

    def browser_handler(self, browsers):
        if len(browsers) == 0:
            self.message(Fore.LIGHTRED_EX, 'Could not locate a running browser')
            self.stop()

        if len(browsers) == 1:
            browser = browsers[0]
            self.message(Fore.GREEN, f'{browser[1]} located!')
            self.browser = Browser(browser, self.lang)

        if len(browsers) > 1:
            self.message(Fore.LIGHTCYAN_EX, f'Currently {len(browsers)} browsers running..')
            for i, browser in enumerate(browsers):
                self.message( Fore.WHITE, f'{Fore.CYAN}[{i}]{Fore.RESET} {browser[1]}')
            option = self.select_browser(len(browsers))
            self.message(Fore.CYAN, f'You selected: {browsers[option][1]}')
            self.browser = Browser(browsers[option], self.lang)

    def connect_rpc(self):
        try:
            self.rpc = Presence(self.client_id, pipe=0)
            self.rpc.connect()
        except exceptions.DiscordNotFound:
            self.message(Fore.LIGHTRED_EX, 'Discord not running', toast=True, s=5)
            self.stop()
        except Exception as e:
            self.message(Fore.RED, e)
        self.message(Fore.LIGHTGREEN_EX, 'Successfully connected', toast=True)

    def get_token(self, title):
        for token in TOKENS[0]:
            if token in title:
                return 'Browsing in ' + token
        return None

    def twitch_handler(self, title):
        img = "logo"
        state = start_time = button = streamer = None
        details = self.get_token(title)
        if not details:
            streamer = title.split(" ")[0]
            mod = "'s" in streamer
            details = 'Watching ' + streamer if not mod else 'Moderating ' + streamer[:-2]
            state = "No Biography" if not self.get_streamer_bio(streamer) else self.get_streamer_bio(streamer)
            button = [{"label": "Go to stream", "url": self.get_url(title)}, {"label": "Download App", "url": "https://manucabral.github.io/TwitchRPC"}]
            if streamer != self.prev_streamer:
                self.start_time = time()
                self.prev_streamer = streamer
        return {
            'state': state,
            'details': details,
            'start': self.start_time,
            'large_image': img,
            'large_text': streamer,
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

    def get_system_lang(self):
        lang = check_output('powershell get-uiculture', universal_newlines=True, stderr=PIPE).split('\n')[3][17:].split('           ')
        self.lang = lang[0]
        self.full_lang = lang[1][1:]
        if not self.lang:
            self.message(Fore.RED, "Error on get your system language")
        self.message(Fore.GREEN, f"Language detected {self.full_lang}")
    
    def run(self):
        system('cls')
        if not self.running:
            self.init_settings()
            self.message(Fore.YELLOW, 'Checking your system language..')
            self.get_system_lang()
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
            self.message(Fore.LIGHTRED_EX, 'Connection lost, re-connecting in 5 seconds..', toast=True)
            sleep(5)
            self.run()