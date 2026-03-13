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
version = "2.1"
version_url = "https://raw.githubusercontent.com/Rekt05/hitman-racetime-automation-snr/refs/heads/main/current_version.txt"
releases_url = "https://github.com/Rekt05/hitman-racetime-automation-snr/releases/latest"

#config
obshost = "localhost"
obsport = 4455

#scene and source info
scenes = ["Streams 1-6", "Streams 7-12", "Streams 13-18"]

twitchlink = "https://player.twitch.tv/?channel={}&enableExtensions=true&muted=false&parent=twitch.tv&player=popout&quality=720p60&volume=0.7699999809265137"
twitchregex = re.compile(r'(?:https?://)?(?:www\.)?twitch\.tv/([a-zA-Z0-9_]+)')

class RacetimeAutomation:
    def __init__(self, root):
        self.root = root
        self.root.title("SNR Racetime Automation")
        self.root.geometry("950x1000") 
        
        self.ws = None
        self.is_monitoring = False
        self.slots = []
        self.scenemap = {scene: {} for scene in scenes} 
        self.blacklist = {} 
        self.lastrt = [] 

        self.current_layout_state = {scene: 0 for scene in scenes}

        #gui vars
        self.urlvar = tk.StringVar()
        self.ratio_var = tk.StringVar(value="16:9")
        self.auto_remove_finished = tk.BooleanVar(value=False)
        self.btn_auto_remove = None
        self.auto_resize_active = tk.BooleanVar(value=False)
        self.btn_auto_resize = None
        self.remove_delay_var = tk.StringVar(value="10")
        self.remove_delay_var.trace_add("write", lambda *args: self.update_button_text())
        self.name_height_var = tk.StringVar(value=75)

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
        racesection = ttk.LabelFrame(root, text="Race Configuration", padding=(10, 5))
        racesection.pack(fill="x", padx=10, pady=2)

        ttk.Label(racesection, text="Racetime URL:").grid(row=0, column=0, sticky="w")
        ttk.Entry(racesection, textvariable=self.urlvar, width=50).grid(row=0, column=1, padx=5, sticky="w")
        ttk.Button(racesection, text="Find Current Race", command=self.get_current).grid(row=0, column=2, padx=2, sticky="w")

        #stream config section
        configsection = ttk.LabelFrame(root, text="Stream Configurations", padding=(10, 5))
        configsection.pack(fill="x", padx=10, pady=2)

        ratio_frame = ttk.Frame(configsection)
        ratio_frame.grid(row=0, column=0, sticky="w", pady=2)
        
        ttk.Label(ratio_frame, text="Aspect Ratio:").pack(side="left", padx=(0, 2))
        self.btn_169 = ttk.Button(ratio_frame, text="[X] 16:9", width=10, command=lambda: self.set_global_ratio("16:9"))
        self.btn_169.pack(side="left", padx=2)
        self.btn_1610 = ttk.Button(ratio_frame, text="[ ] 16:10", width=10, command=lambda: self.set_global_ratio("16:10"))
        self.btn_1610.pack(side="left", padx=2)

        reset_frame = ttk.Frame(configsection)
        reset_frame.grid(row=1, column=0, sticky="w", pady=2)

        ttk.Label(reset_frame, text="Name Height:").pack(side="left", padx=(0, 2))
        vcmd_height = (self.root.register(self.validate_height), '%P')
        self.height_entry = ttk.Entry(reset_frame, textvariable=self.name_height_var, width=6, validate='key', validatecommand=vcmd_height)
        self.height_entry.pack(side="left", padx=2)

        ttk.Button(reset_frame, text="Reset All Positions", command=self.reset_stream_positions).pack(side="left", padx=(2, 2))
        ttk.Button(reset_frame, text="Refresh All Streams", command=self.refresh_all_streams).pack(side="left", padx=2)

        auto_frame = ttk.Frame(configsection)
        auto_frame.grid(row=2, column=0, sticky="w", pady=2)

        ttk.Label(auto_frame, text="Finished Timer:").pack(side="left", padx=(0, 2))
        vcmd_timer = (self.root.register(self.validate_timer), '%P')
        self.delay_entry = ttk.Entry(auto_frame, textvariable=self.remove_delay_var, width=6, validate='key', validatecommand=vcmd_timer)
        self.delay_entry.pack(side="left", padx=2)

        self.btn_auto_remove = ttk.Button(auto_frame, text="[ ] Auto Remove Finished", command=self.toggle_auto_remove)
        self.btn_auto_remove.pack(side="left", padx=(2, 2))

        self.btn_auto_resize = ttk.Button(auto_frame, text="[ ] Auto Resize Streams", command=self.toggle_auto_resize)
        self.btn_auto_resize.pack(side="left", padx=2)

        #player section
        playersection = ttk.Frame(root)
        playersection.pack(fill="both", expand=True, padx=10, pady=5)

        #player slots
        slots_frame = ttk.LabelFrame(playersection, text="Player Slots (1-18)", padding=10)
        slots_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        for i in range(1, 19):
            if i in [1, 7, 13]:
                scene_name = "Streams 1-6" if i==1 else "Streams 7-12" if i==7 else "Streams 13-18"
                
                if i > 1:
                    ttk.Separator(slots_frame, orient='horizontal').pack(fill='x', pady=10)
                
                ctrl_frame = ttk.Frame(slots_frame)
                ctrl_frame.pack(fill="x", pady=5)
                ttk.Label(ctrl_frame, text=f"{scene_name} Layout:", font=('Helvetica', 9, 'bold')).pack(side="left", padx=5)
                
                for count in [6, 4, 2, 1]:
                    btn = ttk.Button(ctrl_frame, text=f"{count}P", width=4, 
                                    command=lambda s=scene_name, c=count: self.set_layout(s, c))
                    btn.pack(side="left", padx=2)

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

    def validate_timer(self, P):
        if P == "": return True
        if P.isdigit():
            val = int(P)
            return 0 <= val <= 45
        return False

    def get_remove_delay(self):
        try:
            return int(self.remove_delay_var.get())
        except ValueError:
            return 10
        
    def validate_height(self, P):
        if P == "": return True
        if P.isdigit():
            val = int(P)
            return 0 <= val <= 100
        return False

    def get_name_height(self):
        try:
            return float(self.name_height_var.get())
        except ValueError:
            return 75.0
        
    def update_button_text(self):
        state = "[X]" if self.auto_remove_finished.get() else "[ ]"
        timer = self.remove_delay_var.get() or "0"
        self.btn_auto_remove.config(text=f"{state} Auto Remove Finished [{timer}s]")

    def set_global_ratio(self, ratio):
        self.ratio_var.set(ratio)
        if ratio == "16:9":
            self.btn_169.config(text="[X] 16:9")
            self.btn_1610.config(text="[ ] 16:10")
        else:
            self.btn_169.config(text="[ ] 16:9")
            self.btn_1610.config(text="[X] 16:10")
        self.log(f"Global Aspect Ratio set to {ratio}")

    def set_layout(self, scene_name, player_count):
        if not self.ws:
            messagebox.showwarning("Connection Error", "Connect to OBS first.")
            return

        canvas_width = 1920
        max_height = 806 
        gap = 3
        padding = 5

        selected_ratio = self.ratio_var.get()
        ratio_w, ratio_h = (16, 10) if selected_ratio == "16:10" else (16, 9)

        layout_map = {6: (3, 2), 4: (2, 2), 2: (2, 1), 1: (1, 1)}
        cols, rows = layout_map[player_count]

        cell_width = (canvas_width - (gap * 2) - (gap * (cols - 1))) / cols
        cell_height = (max_height - (gap * 2) - (gap * (rows - 1))) / rows

        s_width = cell_width
        s_height = (s_width / ratio_w) * ratio_h

        if s_height > cell_height:
            s_height = cell_height
            s_width = (s_height / ratio_h) * ratio_w

        x_offset = (cell_width - s_width) / 2
        y_offset = (cell_height - s_height) / 2

        try:
            resp = self.ws.call(obs_requests.GetSceneItemList(sceneName=scene_name))
            items = resp.getSceneItems()
            scene_slots = [s for s in self.slots if s['scene'] == scene_name]

            for idx, slot in enumerate(scene_slots):
                if idx >= player_count: continue

                col = idx % cols
                row = idx // cols
                sx = gap + (col * (cell_width + gap)) + x_offset
                sy = gap + (row * (cell_height + gap)) + y_offset

                sid = next((i['sceneItemId'] for i in items if i['sourceName'] == slot['browsersource']), None)
                if sid is not None:
                    name_height = self.get_name_height()

                    self.ws.call(obs_requests.SetSceneItemTransform(
                        sceneName=scene_name, sceneItemId=sid,
                        sceneItemTransform={
                            "positionX": float(sx), "positionY": float(sy),
                            "boundsType": "OBS_BOUNDS_STRETCH",
                            "boundsWidth": float(s_width), "boundsHeight": float(s_height),
                            "alignment": 5
                        }
                    ))

                nid = next((i['sceneItemId'] for i in items if i['sourceName'] == slot['textsource']), None)
                if nid is not None:
                    self.ws.call(obs_requests.SetSceneItemTransform(
                        sceneName=scene_name, 
                        sceneItemId=nid,
                        sceneItemTransform={
                            "positionX": float(sx + s_width - padding),
                            "positionY": float(sy + padding),
                            "alignment": 6, "boundsAlignment": 6,
                            "boundsType": "OBS_BOUNDS_SCALE_INNER",
                            "boundsWidth": float(s_width - (padding * 2)),
                            "boundsHeight": name_height,
                            "cropLeft": 0, "cropRight": 0, "cropTop": 0, "cropBottom": 0,
                            "scaleX": 1.0, "scaleY": 1.0
                        }
                    ))
            self.log(f"{scene_name} -> {player_count}P ({selected_ratio})")
        except Exception as e:
            self.log(f"Layout Error: {e}")

    def reset_stream_positions(self):
            for scene in ["Streams 1-6", "Streams 7-12", "Streams 13-18"]:
                self.set_layout(scene, 6)

    def toggle_auto_resize(self):
        new_val = not self.auto_resize_active.get()
        self.auto_resize_active.set(new_val)
        state = "[X]" if new_val else "[ ]"
        self.btn_auto_resize.config(text=f"{state} Auto Resize Streams")
        self.log(f"Auto Resize: {'Enabled' if new_val else 'Disabled'}")

    def auto_adjust_layouts(self):
        if not self.auto_resize_active.get():
            return

        for scene_name in scenes:
            active_count = sum(1 for slot in self.slots 
                            if slot['scene'] == scene_name and slot['namevar'].get().strip())
            
            if active_count >= 5: layout = 6
            elif active_count >= 3: layout = 4
            elif active_count == 2: layout = 2
            elif active_count == 1: layout = 1
            else: layout = None

            if layout and layout != self.current_layout_state.get(scene_name):
                self.set_layout(scene_name, layout)
                self.current_layout_state[scene_name] = layout
        
    def cache_scene_items(self):
        self.scenemap = {scene: {} for scene in scenes}
        for scene in scenes:
            try:
                resp = self.ws.call(obs_requests.GetSceneItemList(sceneName=scene))
                items = resp.getSceneItems()
                for item in items:
                    name = item.get('sourceName')
                    iid = item.get('sceneItemId')
                    self.scenemap[scene][name] = iid
            except Exception as e:
                self.log(f"Cache error: {e}")

    def get_item_id(self, scene, sourcename):
        return self.scenemap.get(scene, {}).get(sourcename)

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
        scene_name = slot['scene']
        streamer_name = entrant['user']['name']
        
        self.ws.call(obs_requests.SetInputSettings(
            inputName=slot['textsource'], 
            inputSettings={"text": streamer_name}
        ))
        
        if 'twitch_channel' in entrant['user']:
            channel_name = self.get_name(entrant['user']['twitch_channel']) 
            if channel_name:
                new_url = twitchlink.format(channel_name)
                self.ws.call(obs_requests.SetInputSettings(inputName=slot['browsersource'], inputSettings={"url": new_url}))
        
        self.manage_visibility(slot_index=slot['index']-1)
        self.log(f"Slot {slot['index']} updated: {streamer_name}")

    def update_obs_name(self, slot, newname):
        if self.ws:
            self.ws.call(obs_requests.SetInputSettings(inputName=slot['textsource'], inputSettings={"text": newname}))

    #gui setup
    def create_slot(self, parent, i):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=2)
        
        if 1 <= i <= 6: scene_name = "Streams 1-6"
        elif 7 <= i <= 12: scene_name = "Streams 7-12"
        else: scene_name = "Streams 13-18"

        slot_data = {
            "index": i,
            "namevar": tk.StringVar(),
            "statuslbl": ttk.Label(frame, text="Empty", width=15),
            "scene": scene_name,
            "textsource": f"Streamer Name {i}",
            "browsersource": f"Stream {i}",
            "finishtime": None
        }

        #buttons
        upbtn = ttk.Button(frame, text="Up", width=8, command=lambda idx=i-1: self.shift_player(idx, "up"))
        upbtn.pack(side="left")
        downbtn = ttk.Button(frame, text="Down", width=8, command=lambda idx=i-1: self.shift_player(idx, "down"))
        downbtn.pack(side="left")
        trashbtn = ttk.Button(frame, text="Remove", width=8, command=lambda idx=i-1: self.remove_player(idx))
        trashbtn.pack(side="left") 
        refreshbtn = ttk.Button(frame, text="Refresh", width=8, command=lambda idx=i-1: self.refresh_single_stream(idx))
        refreshbtn.pack(side="left")

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
        self.manage_visibility(slot_index=emptyslots) 
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
        active_timers = {s['namevar'].get().lower(): s['finishtime'] 
                         for s in self.slots if s['namevar'].get()}

        for i, newname in enumerate(newnames):
            oldname = self.slots[i]['namevar'].get()
            
            if oldname != newname:
                self.slots[i]['namevar'].set(newname)
                
                if newname:
                    self.slots[i]['finishtime'] = active_timers.get(newname.lower())
                    self.update_shift(self.slots[i], newname)
                else:
                    self.slots[i]['finishtime'] = None
                    self.update_obs_name(self.slots[i], "")
                
                self.manage_visibility(slot_index=i) 
    
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
                self.manage_visibility() 
                self.is_monitoring = True
                self.btn_connect.config(text="Stop")
                threading.Thread(target=self.monitor_loop, daemon=True).start() 
                self.root.after(1000, self.smooth_timer_loop)
            except Exception as e:
                messagebox.showerror("Connection Error", f"{e}")
        else:
            self.is_monitoring = False
            if self.ws: self.ws.disconnect()
            self.btn_connect.config(text="Start")
            self.log("Stopped")

    def toggle_auto_remove(self):
        new_val = not self.auto_remove_finished.get()
        self.auto_remove_finished.set(new_val)
        self.update_button_text()
        self.log(f"Auto Remove: {'Enabled' if new_val else 'Disabled'}")

    def remove_finished_players(self, entrants):
        if not self.auto_remove_finished.get():
            return
        
        for e in entrants:
            status = e.get('status', {}).get('value')
            if status in ['done', 'dnf']:
                pname = e['user']['name']
                for slot in self.slots:
                    if slot['namevar'].get().lower() == pname.lower():
                        if slot['finishtime'] is None:
                            slot['finishtime'] = time.time()
                            self.log(f"Countdown started for {pname}")
                        break

    def monitor_loop(self):
        while self.is_monitoring:
            url = self.urlvar.get().strip()
            if not url:
                time.sleep(1); continue
            
            if not url.endswith("/data"): url += "/data"
            try:
                r = requests.get(url, timeout=4)
                if r.status_code != 200:
                    self.log(f"API Error: {r.status_code}")
                    time.sleep(5); continue
                    
                data = r.json()
                entrants = data.get('entrants', [])
                self.lastrt = entrants

                self.remove_finished_players(entrants)
                
                nameslower = {s['namevar'].get().lower() for s in self.slots if s['namevar'].get()}
                blacklisted = set(self.blacklist.keys())
                
                for entrant in entrants:
                    pname = entrant['user']['name']
                    if pname.lower() not in nameslower and pname.lower() not in blacklisted:
                        for slot in self.slots:
                            if not slot['namevar'].get():
                                slot['namevar'].set(pname)
                                self.update_obs(slot, entrant)
                                nameslower.add(pname.lower())
                                break

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
                            lbl = f"Finished: {place}"
                            if slot['finishtime']: lbl += " (10s)"
                            slot['statuslbl'].config(text=lbl, style="Done.TLabel")
                        elif status == "dnf":
                            lbl = "DNF"
                            if slot['finishtime']: lbl += " (10s)"
                            slot['statuslbl'].config(text=lbl, style="DNF.TLabel")
                        else:
                            slot['statuslbl'].config(text="Racing", style="Racing.TLabel")
                            slot['finishtime'] = None

                self.auto_adjust_layouts()
                self.manage_visibility()

                self.log(f"Synced at {time.strftime('%H:%M:%S')}")

            except Exception as e:
                self.log(f"Sync error: {e}")
                
            time.sleep(5)

    def manage_visibility(self, slot_index=None):
        if not self.ws: return
        
        target_slots = [self.slots[slot_index]] if slot_index is not None else self.slots
        
        for slot in target_slots:
            scene_name = slot['scene']
            is_active = bool(slot['namevar'].get().strip())
            
            try:
                resp = self.ws.call(obs_requests.GetSceneItemList(sceneName=scene_name))
                items = resp.getSceneItems()
                
                for key in ['browsersource', 'textsource']:
                    target_source_name = slot[key]
                    
                    iid = next((item['sceneItemId'] for item in items 
                               if item['sourceName'] == target_source_name), None)
                    
                    if iid is not None:
                        self.ws.call(obs_requests.SetSceneItemEnabled(
                            sceneName=scene_name, 
                            sceneItemId=iid, 
                            sceneItemEnabled=is_active
                        ))
            except Exception as e:
                print(f"Error toggling {slot['textsource']} in {scene_name}: {e}")

    def refresh_single_stream(self, index):
        if not self.ws:
            return
        
        slot = self.slots[index]
        source_name = slot['browsersource']
        
        try:
            resp = self.ws.call(obs_requests.GetInputSettings(inputName=source_name))
            current_settings = resp.getInputSettings()
            original_url = current_settings.get('url')
            
            if original_url:
                self.ws.call(obs_requests.SetInputSettings(
                    inputName=source_name,
                    inputSettings={'url': 'about:blank'}
                ))
                
                self.root.after(100, lambda: self.ws.call(obs_requests.SetInputSettings(
                    inputName=source_name,
                    inputSettings={'url': original_url}
                )))
                
                self.log(f"Refreshing: {slot['namevar'].get()}")
        except Exception as e:
            self.log(f"Refresh failed: {e}")

    def refresh_all_streams(self):
        if not self.ws:
            messagebox.showwarning("Connection Error", "Connect to OBS first.")
            return
            
        for i in range(len(self.slots)):
            if self.slots[i]['namevar'].get().strip():
                self.root.after(i * 150, lambda idx=i: self.refresh_single_stream(idx))
        
        self.log("Refreshing all streams.")

    def smooth_timer_loop(self):
        if not self.is_monitoring:
            return

        current_time = time.time()
        to_remove = []
        
        max_delay = self.get_remove_delay()

        for i, slot in enumerate(self.slots):
            pname = slot['namevar'].get().strip()
            if not pname or slot['finishtime'] is None:
                continue

            elapsed = current_time - slot['finishtime']
            remaining = max(0, max_delay - int(elapsed))

            current_text = slot['statuslbl'].cget("text")
            if "(" in current_text:
                base_text = current_text.split(" (")[0]
                slot['statuslbl'].config(text=f"{base_text} ({remaining}s)")
            elif "Finished" in current_text or "DNF" in current_text:
                slot['statuslbl'].config(text=f"{current_text} ({remaining}s)")

            if remaining <= 0:
                to_remove.append(i)

        if to_remove:
            for index in sorted(to_remove, reverse=True):
                self.remove_player(index)
                self.slots[index]['finishtime'] = None
            
            self.auto_adjust_layouts()
            self.manage_visibility()

        self.root.after(1000, self.smooth_timer_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = RacetimeAutomation(root)
    root.mainloop()