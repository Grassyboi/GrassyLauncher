import os, subprocess, threading, sys, urllib.request, tempfile, customtkinter as ctk
from tkinter import messagebox

if sys.platform == "win32":
    try: import ctypes; ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("grassy.launcher.offline.v1")
    except: pass

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

if getattr(sys, 'frozen', False): BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else: BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MINECRAFT_DIR = os.path.join(BASE_DIR, "minecraft_data")
os.makedirs(MINECRAFT_DIR, exist_ok=True)

try: import minecraft_launcher_lib
except ImportError:
    messagebox.showerror("Dependency Error", "Please install dependencies:\npip install customtkinter minecraft-launcher-lib")
    sys.exit()

def optimize_game_settings():
    try:
        opts_path = os.path.join(MINECRAFT_DIR, "options.txt")
        settings = {}
        if os.path.exists(opts_path):
            with open(opts_path, "r") as f:
                for line in f:
                    if ":" in line: k, v = line.strip().split(":", 1); settings[k] = v
        settings.update({
            "enableVsync": "false", "maxFps": "260", "renderDistance": "6", 
            "simulationDistance": "5", "graphicsMode": "0", "ao": "0", 
            "clouds": "false", "bobView": "false", "particles": "2"
        })
        with open(opts_path, "w") as f:
            for k, v in settings.items(): f.write(f"{k}:{v}\n")
    except: pass

class GrassyLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Grassy Launcher")
        self.geometry("460x650")
        self.resizable(False, False)
        self.filtered_versions = []
        self.load_web_icon()

        ctk.CTkLabel(self, text="GRASSY LAUNCHER", font=ctk.CTkFont(family="Helvetica", size=24, weight="bold"), text_color="#52be80").pack(pady=(15, 2))
        ctk.CTkLabel(self, text="Cracked Minecraft", font=ctk.CTkFont(family="Helvetica", size=12, slant="italic"), text_color="gray").pack(pady=(0, 10))

        f1 = ctk.CTkFrame(self, fg_color="transparent"); f1.pack(pady=4)
        ctk.CTkLabel(f1, text="Username:", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
        self.username_entry = ctk.CTkEntry(f1, placeholder_text="Enter username...", width=200, height=35)
        self.username_entry.insert(0, "Player"); self.username_entry.pack(side="left", padx=10)

        f2 = ctk.CTkFrame(self, fg_color="transparent"); f2.pack(pady=4)
        ctk.CTkLabel(f2, text="Version:", font=ctk.CTkFont(size=14)).pack(side="left", padx=15)
        self.version_option = ctk.CTkOptionMenu(f2, values=["Fetching..."], width=200, height=35, fg_color="#52be80", button_color="#45b374", button_hover_color="#3da86a")
        self.version_option.pack(side="left", padx=10)

        self.cosmetics_frame = ctk.CTkFrame(self, fg_color="transparent"); self.cosmetics_frame.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(self.cosmetics_frame, text="Skin (Minecraft Username)", font=ctk.CTkFont(size=12, weight="bold"), text_color="#52be80").pack(pady=(2, 2))
        self.skin_entry = ctk.CTkEntry(self.cosmetics_frame, placeholder_text="Enter MC Username for skin...", width=360, height=35)
        self.skin_entry.pack(pady=3)

        ctk.CTkLabel(self.cosmetics_frame, text="Select Cape Style", font=ctk.CTkFont(size=12, weight="bold"), text_color="#52be80").pack(pady=(4, 2))
        capes = ["None", "Minecon 2011", "Minecon 2012", "Minecon 2013", "Minecon 2015", "Minecon 2016", "Optifine", "Mojang Studios", "Mojang Classic", "Vanilla Cape", "Migrator", "Cherry Blossom", "15th Anniversary", "Purple Heart (Twitch)", "Follower's (TikTok)", "MCC 15th Year", "Realms Mapmaker", "Mojira Moderator", "Cobalt", "Scrolls Champion", "Translator"]
        self.cape_option = ctk.CTkOptionMenu(self.cosmetics_frame, values=capes, width=360, height=35, fg_color="#52be80", button_color="#45b374", button_hover_color="#3da86a")
        self.cape_option.set("None"); self.cape_option.pack(pady=3)

        self.ram_frame = ctk.CTkFrame(self, fg_color="transparent"); self.ram_frame.pack(pady=5, padx=20, fill="x")
        self.ram_label = ctk.CTkLabel(self.ram_frame, text="Allocated RAM: 2 GB", font=ctk.CTkFont(size=12, weight="bold"), text_color="#52be80")
        self.ram_label.pack()
        self.ram_slider = ctk.CTkSlider(self.ram_frame, from_=1, to=8, number_of_steps=7, command=self.update_ram_label, button_color="#45b374", button_hover_color="#3da86a", progress_color="#52be80")
        self.ram_slider.set(2); self.ram_slider.pack(pady=3)

        self.util_frame = ctk.CTkFrame(self, fg_color="transparent"); self.util_frame.pack(pady=5)
        self.folder_btn = ctk.CTkButton(self.util_frame, text="📁 Open Game Folder", font=ctk.CTkFont(size=11), width=150, height=30, fg_color="#34495e", hover_color="#2c3e50", command=lambda: os.startfile(MINECRAFT_DIR))
        self.folder_btn.pack(side="left", padx=10)
        
        self.theme_switch = ctk.CTkSwitch(self.util_frame, text="Dark Mode", font=ctk.CTkFont(size=11), command=self.toggle_theme, progress_color="#52be80")
        self.theme_switch.select(); self.theme_switch.pack(side="left", padx=10)

        self.notice_label = ctk.CTkLabel(self, text="⚠️ NOTICE: Cosmetics only apply on cracked multiplayer servers supporting custom wrappers. Won't display in vanilla singleplayer.", font=ctk.CTkFont(size=10, slant="italic"), text_color="#e59866", wraplength=380)
        self.notice_label.pack(pady=5)

        self.launch_button = ctk.CTkButton(self, text="LAUNCH GAME", font=ctk.CTkFont(size=14, weight="bold"), width=220, height=40, corner_radius=8, fg_color="#52be80", hover_color="#45b374", command=self.start_launch_thread)
        self.launch_button.pack(pady=10)

        self.status_label = ctk.CTkLabel(self, text="Ready to play", font=ctk.CTkFont(size=12), text_color="#555555"); self.status_label.pack()
        threading.Thread(target=self.load_versions, daemon=True).start()

    def update_ram_label(self, value):
        self.ram_label.configure(text=f"Allocated RAM: {int(value)} GB")

    def toggle_theme(self):
        ctk.set_appearance_mode("Dark" if self.theme_switch.get() == 1 else "Light")

    def load_web_icon(self):
        url = "https://raw.githubusercontent.com/Grassyboi/GrassyLauncher/refs/heads/main/GrassyLauncher.ico"
        if hasattr(sys, '_MEIPASS'):
            path = os.path.join(sys._MEIPASS, "GrassyLauncher.ico")
            if os.path.exists(path):
                try: self.iconbitmap(default=path); return
                except: pass
        tmp = os.path.join(os.path.abspath(tempfile.gettempdir()), "temp_grassy_icon.ico")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as res:
                with open(tmp, "wb") as f: f.write(res.read())
            self.iconbitmap(default=tmp)
        except Exception as e: print(f"[ICON NOTICE]: {e}")

    def load_versions(self):
        fallbacks = ["26.2", "26.1", "1.20.1", "1.19.4", "1.16.5", "1.12.2", "1.8.9"]
        try:
            all_v = minecraft_launcher_lib.utils.get_version_list()
            rels = [v['id'] for v in all_v if v['type'] == 'release']
            try: self.filtered_versions = rels[rels.index("26.2") : rels.index("1.8.9") + 1]
            except: self.filtered_versions = fallbacks
        except: self.filtered_versions = fallbacks
        self.after(0, self.update_version_menu)

    def update_version_menu(self):
        self.version_option.configure(values=self.filtered_versions)
        if self.filtered_versions: self.version_option.set(self.filtered_versions[0])

    def update_status(self, text, color=None):
        self.status_label.configure(text=text)
        if color: self.status_label.configure(text_color=color)

    def start_launch_thread(self):
        user = self.username_entry.get().strip()
        if not user: messagebox.showerror("Error", "Please enter a username!"); return
        ver = self.version_option.get()
        if ver == "Fetching...": messagebox.showwarning("Warning", "Please wait for the version list to load!"); return
        self.launch_button.configure(state="disabled"); self.username_entry.configure(state="disabled")
        self.version_option.configure(state="disabled"); self.skin_entry.configure(state="disabled")
        self.cape_option.configure(state="disabled"); self.ram_slider.configure(state="disabled")
        threading.Thread(target=self.launch_game, args=(user, ver), daemon=True).start()

    def launch_game(self, username, version):
        self.update_status("Preparing files...", "#52be80")
        cb = {"setStatus": lambda s: self.update_status(f"Downloading: {(s.split('/')[-1] if '/' in s else s)[:25]}...", "#e59866")}
        try:
            self.update_status("Evaluating Java resources...", "#52be80")
            java_path = None
            try:
                minecraft_launcher_lib.runtime.install_jvm_runtime(version, MINECRAFT_DIR, callback=cb)
                java_path = minecraft_launcher_lib.runtime.get_executable_path(version, MINECRAFT_DIR)
            except: pass
            
            self.update_status(f"Downloading Minecraft {version}...", "#e59866")
            minecraft_launcher_lib.install.install_minecraft_version(version, MINECRAFT_DIR, callback=cb)
            
            self.update_status("Applying system optimizations...", "#52be80")
            optimize_game_settings()
            
            self.update_status("Starting Minecraft...", "#2ecc71")
            opts = {"username": username, "uuid": "00000000-0000-0000-0000-000000000000", "token": "0"}
            if java_path: opts["executablePath"] = java_path
            
            ram_max = f"-Xmx{int(self.ram_slider.get())}G"
            jvm_args = [ram_max, "-Xms512M", "-Dminecraft.api.auth.host=localhost"]
            
            skin_user = self.skin_entry.get().strip()
            if skin_user: jvm_args.append(f"-Dgrassy.skin={skin_user}")
            
            selected_cape = self.cape_option.get()
            if selected_cape != "None": jvm_args.append(f"-Dgrassy.cape={selected_cape.replace(' ', '_')}")
            opts["jvmArguments"] = jvm_args

            cmd = minecraft_launcher_lib.command.get_minecraft_command(version, MINECRAFT_DIR, opts)
            self.after(0, self.withdraw)
            subprocess.run(cmd)
            self.after(0, self.deiconify)
            self.after(0, lambda: self.update_status("Welcome back!", "#2ecc71"))
        except Exception as e:
            err_msg = str(e)
            self.after(0, self.deiconify)
            self.after(0, lambda: self.update_status("Launch Failed", "#e74c3c"))
            self.after(0, lambda msg=err_msg: messagebox.showerror("Error", f"Failed to run Minecraft:\n{msg}"))
        finally:
            self.after(0, lambda: self.launch_button.configure(state="normal"))
            self.after(0, lambda: self.username_entry.configure(state="normal"))
            self.after(0, lambda: self.version_option.configure(state="normal"))
            self.after(0, lambda: self.skin_entry.configure(state="normal"))
            self.after(0, lambda: self.cape_option.configure(state="normal"))
            self.after(0, lambda: self.ram_slider.configure(state="normal"))

if __name__ == "__main__":
    app = GrassyLauncher()
    app.mainloop()