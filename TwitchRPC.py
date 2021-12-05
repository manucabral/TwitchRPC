from subprocess import check_output
from sqlite3 import connect
from os import system, getenv, path
from shutil import copy2
from pypresence import Presence
from time import time, sleep

class Browser:
    def __init__(self, name, full_name, process_name, local_path):
        self.name = name
        self.full_name = full_name
        self.process_name = process_name
        self.path = getenv("LOCALAPPDATA") + local_path
        self.db_file = "\\History"

    def running(self):
        output = check_output(f'wmic process where "name=\'{self.process_name}\'" get ExecutablePath', universal_newlines=True, stderr=subprocess.PIPE)
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
        self.rpc = Presence(client_id, pipe=0)
        self.running = False

    def is_twitch(self, title):
        return True if "twitch" in title.lower() else False

    def run(self):
        try:
            self.rpc.connect()
        except Exception as e:
            print(f'An error occurred {e}')

        print("TwitchRPC connected!")
        self.running = True
        previous_streamer = None

        while self.running:
            title, url = self.browser.current_website()
            streamer = title.split(" ")[0]
            try:
                if self.is_twitch(title):
                    if streamer != previous_streamer:
                        start_time = time()
                        previous_streamer = streamer
                    self.rpc.update(details='Watching ' + title.split(" ")[0], start=start_time)
                else:
                    self.rpc.update(details='Off twitch :/')
            except:
                self.rpc.close()
            sleep(15)


client = TwitchRPC(":D")
client.run()
