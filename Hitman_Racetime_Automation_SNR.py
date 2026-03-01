import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import time
import re
from obswebsocket import obsws, requests as obs_requests
import configparser
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_external_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

#version config
version = "1.2"
version_url = "https://raw.githubusercontent.com/Rekt05/hitman-racetime-automation-snr/refs/heads/main/current_version.txt"
releases_url = "https://github.com/Rekt05/hitman-racetime-automation-snr/releases/latest"

#config
obshost = "localhost"
obsport = 4455

#scene and source info
scene16 = "Streams 1-6"
scene712 = "Streams 7-12"
scene1318 = "Streams 13-18"

twitchlink = "https://player.twitch.tv/?channel={}&enableExtensions=true&muted=false&parent=twitch.tv&player=popout&quality=720p60&volume=0.7699999809265137"
twitchregex = re.compile(r'(?:https?://)?(?:www\.)?twitch\.tv/([a-zA-Z0-9_]+)')

class RacetimeAutomation:
    def __init__(self, root):
        self.root = root
        self.root.title("SNR Racetime Automation")
        self.root.geometry("900x750") 
        
        self.ws = None
        self.is_monitoring = False
        self.slots = []
        self.scenemap = {} 
        self.blacklist = {} 
        self.lastrt = [] 

        #gui vars
        self.urlvar = tk.StringVar()
        
        #password
        self.config = configparser.ConfigParser()
        config_file = get_external_path("config.ini")
        if os.path.exists(config_file):
            self.config.read(config_file)
            
        savedpw = self.config.get("Settings", "OBSPW", fallback="")
        self.pwvar = tk.StringVar(value=savedpw)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close) 

        style = ttk.Style()
        style.configure("Racing.TLabel", foreground="green")
        style.configure("Done.TLabel", foreground="blue", font=('Helvetica', 9, 'bold'))
        style.configure("DNF.TLabel", foreground="red", font=('Helvetica', 9, 'bold'))
        style.configure("Small.TButton", font=('Helvetica', 7))

        #obs connection section
        obssection = ttk.LabelFrame(root, text="OBS Connection", padding=10)
        obssection.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(obssection, text="OBS Password:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(obssection, textvariable=self.pwvar, width=30, show="*").grid(row=0, column=1, padx=5, sticky="ew")

        self.btn_connect = ttk.Button(obssection, text="Start", command=self.toggle_monitoring)
        self.btn_connect.grid(row=0, column=2, padx=5)
        
        #race config section
        racesection = ttk.LabelFrame(root, text="Race Configuration", padding=10)
        racesection.pack(fill="x", padx=10, pady=5)

        ttk.Label(racesection, text="Racetime URL:").grid(row=0, column=0, sticky="w")
        ttk.Entry(racesection, textvariable=self.urlvar, width=40).grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(racesection, text="Find Current Race", command=self.get_current).grid(row=0, column=2, padx=5)
        
        ttk.Button(racesection, text="Reset Stream Positions", command=self.reset_stream_positions).grid(row=0, column=3, padx=5)

        #player section
        playersection = ttk.Frame(root)
        playersection.pack(fill="both", expand=True, padx=10, pady=5)

        #player slots
        slots_frame = ttk.LabelFrame(playersection, text="Player Slots (1-18)", padding=10)
        slots_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        for i in range(1, 19):
            self.create_slot(slots_frame, i)

        #removed players blacklist
        self.blacklistsection = ttk.LabelFrame(playersection, text="Removed Players", padding=10)
        self.blacklistsection.pack(side="right", fill="y", padx=(5, 0))
        
        self.blacklist_container = ttk.Frame(self.blacklistsection)
        self.blacklist_container.pack(fill="both", expand=True)

        self.update_blacklist() 

        self.status_var = tk.StringVar(value="Enter an OBS password and click start")
        self.status_label = ttk.Label(root, textvariable=self.status_var, relief="sunken", style="TLabel")
        self.status_label.pack(side="bottom", fill="x")

        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def reset_stream_positions(self):
        if not self.ws:
            messagebox.showwarning("Connection Error", "Please connect to OBS first.")
            return

        coords = {
            1: (3, 3), 
            2: (642, 3), 
            3: (1281, 3),
            4: (3, 406), 
            5: (642, 406), 
            6: (1281, 406)
        }

        self.cache_scene_items()

        try:
            for slot in self.slots:
                pos_index = ((slot['index'] - 1) % 6) + 1
                x, y = coords[pos_index]

                folder_id = self.get_item_id(slot['scene'], slot['foldersource'])
                if folder_id is not None:
                    self.ws.call(obs_requests.SetSceneItemTransform(
                        sceneName=slot['scene'],
                        sceneItemId=folder_id,
                        sceneItemTransform={
                            "positionX": x,
                            "positionY": y,
                            "boundsType": "OBS_BOUNDS_STRETCH",
                            "boundsWidth": 636,
                            "boundsHeight": 400
                        }
                    ))

                browser_id = self.get_item_id(slot['scene'], slot['browsersource'])
                if browser_id is not None:
                    self.ws.call(obs_requests.SetSceneItemTransform(
                        sceneName=slot['scene'],
                        sceneItemId=browser_id,
                        sceneItemTransform={
                            "positionX": 0,
                            "positionY": 0,
                            "scaleX": 1.0,
                            "scaleY": 1.0,
                            "boundsType": "OBS_BOUNDS_NONE"
                        }
                    ))
            self.log("Positions and sizes reset.")
        except Exception as e:
            self.log(f"Reset failed: {e}")

    def cache_scene_items(self):
        self.scenemap = {}
        for scene in [scene16, scene712, scene1318]:
            self.scenemap[scene] = {}
            try:
                resp = self.ws.call(obs_requests.GetSceneItemList(sceneName=scene))
                items = resp.getSceneItems()
                for item in items:
                    name = item.get('sourceName')
                    iid = item.get('sceneItemId')
                    self.scenemap[scene][name] = iid
            except Exception as e:
                self.log(f"Cache error: {e}")

    def check_for_updates(self):
        ignored = self.config.get("Settings", "IgnoreVersion", fallback="")
        try:
            r = requests.get(version_url, timeout=5)
            if r.status_code == 200:
                latest = r.text.strip()
                if latest != version and latest != ignored:
                    self.root.after(0, lambda: self.show_update_dialog(latest))
        except:
            pass

    def show_update_dialog(self, latest_version):
            update_win = tk.Toplevel(self.root)
            update_win.title("Available Update")
            update_win.geometry("400x130")
            update_win.resizable(False, False)
            update_win.attributes("-topmost", True)
            
            ttk.Label(update_win, text=f"A new update (v{latest_version}) is available.", padding=10).pack()
            
            btn_frame = ttk.Frame(update_win)
            btn_frame.pack(pady=10)

            def open_link():
                import webbrowser
                webbrowser.open(releases_url)
                update_win.destroy()

            def ignore_permanently():
                if 'Settings' not in self.config: 
                    self.config['Settings'] = {}
                self.config['Settings']['IgnoreVersion'] = latest_version
                self.save_config()
                self.log(f"Version {latest_version} will be ignored moving forward.")
                update_win.destroy()

            ttk.Button(btn_frame, text="Go to Page", command=open_link).grid(row=0, column=0, padx=5)
            ttk.Button(btn_frame, text="Ignore Once", command=update_win.destroy).grid(row=0, column=1, padx=5)
            ttk.Button(btn_frame, text="Ignore Permanently", command=ignore_permanently).grid(row=0, column=2, padx=5)

    def get_current(self):
        try:
            r = requests.get("https://racetime.gg/hitman-3/data", timeout=5) #change "hitman-3" to whatever game if needed
            if r.status_code == 200:
                data = r.json()
                active = data.get('current_races', [])
                openr = [race for race in active if race.get('status', {}).get('value') == 'open']
                
                #this gets the first open/active race, not a problem with the frequency of hitman races being only 1 every week, but should ideally be handled by user choice
                if openr:
                    target = openr[0].get('data_url')
                    self.urlvar.set(f"https://racetime.gg{target}")
                    self.log(f"Race found.")
                elif active:
                    target = active[0].get('data_url')
                    self.urlvar.set(f"https://racetime.gg{target}")
                    self.log(f"Active race used.")
                else:
                    self.log("No active hitman-3 races found.")
        except Exception as e:
            self.log(e)

    def save_config(self):
        if 'Settings' not in self.config:
            self.config['Settings'] = {}
        self.config['Settings']['OBSPW'] = self.pwvar.get()
        with open(get_external_path("config.ini"), 'w') as cfgfile:
            self.config.write(cfgfile)

    def on_close(self):
        self.save_config()
        self.is_monitoring = False
        if self.ws:
            self.ws.disconnect()
        self.root.destroy()

    def log(self, msg):
        self.status_var.set(msg)
        print(msg)

    def get_name(self, streamlink):
        if not '/' in streamlink and not '.' in streamlink:
            return streamlink
        match = twitchregex.search(streamlink)
        return match.group(1) if match else ""
    
    def update_obs(self, slot, entrant):
        self.ws.call(obs_requests.SetInputSettings(inputName=slot['textsource'], inputSettings={"text": entrant['user']['name']}))
        if 'twitch_channel' in entrant['user']:
            channel_name = self.get_name(entrant['user']['twitch_channel']) 
            if channel_name:
                new_url = twitchlink.format(channel_name)
                self.ws.call(obs_requests.SetInputSettings(inputName=slot['browsersource'], inputSettings={"url": new_url}))

    def update_obs_name(self, slot, newname):
        if self.ws:
            self.ws.call(obs_requests.SetInputSettings(inputName=slot['textsource'], inputSettings={"text": newname}))

    #gui setup
    def create_slot(self, parent, i):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=2)
        
        slot_data = {
            "index": i,
            "namevar": tk.StringVar(),
            "statuslbl": ttk.Label(frame, text="Empty", width=15),
            "scene": scene16 if 1 <= i <= 6 else (scene712 if 7 <= i <= 12 else scene1318),
            "foldersource": f"Stream #{i}",
            "textsource": f"Streamer Name {i}",
            "browsersource": f"Stream {i}"
        }

        #buttons
        upbtn = ttk.Button(frame, text="▲", width=2, style="Small.TButton", command=lambda idx=i-1: self.shift_player(idx, "up"))
        upbtn.pack(side="left")
        downbtn = ttk.Button(frame, text="▼", width=2, style="Small.TButton", command=lambda idx=i-1: self.shift_player(idx, "down"))
        downbtn.pack(side="left")
        trashbtn = ttk.Button(frame, text="🗑️", width=2, command=lambda idx=i-1: self.remove_player(idx))
        trashbtn.pack(side="left", padx=(5, 5)) 

        ttk.Label(frame, text=f"Slot {i}:", width=10).pack(side="left", padx=(5, 0))
        ttk.Entry(frame, textvariable=slot_data['namevar'], width=15).pack(side="left", padx=5)
        slot_data['statuslbl'].pack(side="left", padx=5)
        
        self.slots.append(slot_data)

    def update_blacklist(self):
        for widget in self.blacklist_container.winfo_children():
            widget.destroy()
        if not self.blacklist:
            ttk.Label(self.blacklist_container, text="No removed players").pack(pady=5, padx=5)
            return
        for lowername, original_name in self.blacklist.items():
            player_section = ttk.Frame(self.blacklist_container)
            player_section.pack(fill="x", pady=2)
            ttk.Button(player_section, text="+", width=2, command=lambda name=original_name: self.readd_player(name)).pack(side="left")
            ttk.Label(player_section, text=original_name, width=15, anchor="w").pack(side="left", padx=5)

    def remove_player(self, index_to_remove):
        playername = self.slots[index_to_remove]['namevar'].get()
        if not playername: return
        lowername = playername.lower()
        if lowername not in self.blacklist:
            self.blacklist[lowername] = playername
            self.update_blacklist()
        currentnames = [slot['namevar'].get() for slot in self.slots]
        nameshift = [name for i, name in enumerate(currentnames) if i > index_to_remove and name]
        newnames = currentnames[:index_to_remove] + nameshift + [""]
        self.new_slot_order(newnames)

    def readd_player(self, playername):
        emptyslots = next((i for i, slot in enumerate(self.slots) if not slot['namevar'].get()), None)
        if emptyslots is None:
            self.log("Slots full")
            return
        self.slots[emptyslots]['namevar'].set(playername)
        self.update_shift(self.slots[emptyslots], playername)
        self.manage_folder_visibility(slot_index=emptyslots) 
        del self.blacklist[playername.lower()]
        self.update_blacklist()

    def shift_player(self, index, direction):
        if not self.slots[index]['namevar'].get(): return 
        targets = index + (1 if direction == "down" else -1)
        if not (0 <= targets < len(self.slots)): return
        currentnames = [slot['namevar'].get() for slot in self.slots]
        currentnames[index], currentnames[targets] = currentnames[targets], currentnames[index]
        self.new_slot_order(currentnames)

    def new_slot_order(self, newnames):
        for i, newname in enumerate(newnames):
            oldname = self.slots[i]['namevar'].get()
            if oldname != newname:
                self.slots[i]['namevar'].set(newname)
                if newname:
                    self.update_shift(self.slots[i], newname)
                else:
                    self.update_obs_name(self.slots[i], "")
                self.manage_folder_visibility(slot_index=i) 
    
    def update_shift(self, slot, playername):
        if not self.ws: return
        entrant = next((e for e in self.lastrt if e['user']['name'].lower() == playername.lower()), None)
        if entrant:
            self.update_obs(slot, entrant)
        else:
            self.update_obs_name(slot, playername)

    def toggle_monitoring(self):
        if not self.is_monitoring:
            try:
                self.ws = obsws(obshost, obsport, self.pwvar.get())
                self.ws.connect()
                self.log("OBS connected")
                self.cache_scene_items() 
                self.manage_folder_visibility(initialize=True) 
                self.is_monitoring = True
                self.btn_connect.config(text="Stop")
                threading.Thread(target=self.monitor_loop, daemon=True).start() 
            except Exception as e:
                messagebox.showerror("Connection Error", f"{e}")
        else:
            self.is_monitoring = False
            if self.ws: self.ws.disconnect()
            self.btn_connect.config(text="Start")
            self.log("Stopped")

    def monitor_loop(self):
        while self.is_monitoring:
            url = self.urlvar.get().strip()
            if not url:
                time.sleep(1); continue
            
            if not url.endswith("/data"): url += "/data"
            try:
                data = requests.get(url, timeout=4).json()
                entrants = data.get('entrants', [])
                self.lastrt = entrants
                
                nameslower = {s['namevar'].get().lower() for s in self.slots if s['namevar'].get()}
                blacklisted = set(self.blacklist.keys())
                
                for entrant in entrants:
                    pname = entrant['user']['name']
                    if pname.lower() not in nameslower and pname.lower() not in blacklisted:
                        for slot in self.slots:
                            if not slot['namevar'].get():
                                slot['namevar'].set(pname)
                                self.update_obs(slot, entrant)
                                self.manage_folder_visibility()
                                nameslower.add(pname.lower()) 
                                break
                
                self.manage_folder_visibility() 

                for slot in self.slots:
                    playername = slot['namevar'].get()
                    if not playername:
                        slot['statuslbl'].config(text="Empty", style="TLabel")
                        continue
                    entrant = next((e for e in entrants if e['user']['name'].lower() == playername.lower()), None)
                    if entrant:
                        status = entrant['status']['value']
                        place = entrant.get('place')
                        if status == "done":
                            slot['statuslbl'].config(text=f"Finished: {place}", style="Done.TLabel")
                        elif status == "dnf":
                            slot['statuslbl'].config(text="DNF", style="DNF.TLabel")
                        else:
                            slot['statuslbl'].config(text="Racing", style="Racing.TLabel")
                    else:
                        slot['statuslbl'].config(text="Not Found", style="TLabel")

                self.log(f"Synced at {time.strftime('%H:%M:%S')}")
            except:
                pass
            time.sleep(5)

    def get_item_id(self, scene, sourcename):
        return self.scenemap.get(scene, {}).get(sourcename)

    def manage_folder_visibility(self, initialize=False, slot_index=None):
        if not self.ws: return
        slotstocheck = [self.slots[slot_index]] if slot_index is not None else self.slots
        for slot in slotstocheck:
            isassigned = bool(slot['namevar'].get())
            if initialize and isassigned: continue
            iid = self.get_item_id(slot['scene'], slot['foldersource'])
            if iid:
                self.ws.call(obs_requests.SetSceneItemEnabled(
                    sceneName=slot['scene'], sceneItemId=iid, sceneItemEnabled=isassigned
                ))

if __name__ == "__main__":
    root = tk.Tk()
    app = RacetimeAutomation(root)
    root.mainloop()