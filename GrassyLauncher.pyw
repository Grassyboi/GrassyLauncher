import os, subprocess, threading, sys, urllib.request, tempfile, shutil, re
import customtkinter as ctk
from tkinter import messagebox

if sys.platform == "win32":
    try: 
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("grassy.launcher.offline.v1")
    except: 
        pass

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

BASE_DIR = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
GAME_DIR = os.path.join(BASE_DIR, "game_assets")
os.makedirs(GAME_DIR, exist_ok=True)

try: 
    import minecraft_launcher_lib
except ImportError:
    messagebox.showerror("Dependency Error", "Please install dependencies:\npip install customtkinter minecraft-launcher-lib")
    sys.exit()

def optimize_game_settings():
    try:
        opts_path = os.path.join(GAME_DIR, "options.txt")
        settings = {}
        if os.path.exists(opts_path):
            with open(opts_path, "r") as f:
                for line in f:
                    if ":" in line: 
                        k, v = line.strip().split(":", 1)
                        settings[k] = v
        settings.update({
            "enableVsync": "false", "maxFps": "260", "renderDistance": "6", 
            "simulationDistance": "5", "graphicsMode": "0", "ao": "0", 
            "clouds": "false", "bobView": "false", "particles": "2"
        })
        with open(opts_path, "w") as f:
            for k, v in settings.items(): 
                f.write(f"{k}:{v}\n")
    except: 
        pass

class GrassyLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Grassy Launcher")
        self.geometry("400x480")
        self.resizable(False, False)
        self.filtered_versions = []
        self.load_web_icon()

        ctk.CTkLabel(self, text="GRASSY LAUNCHER", font=ctk.CTkFont(family="Helvetica", size=24, weight="bold"), text_color="#52be80").pack(pady=(20, 2))
        ctk.CTkLabel(self, text="Cracked Minecraft Launcher", font=ctk.CTkFont(family="Helvetica", size=12, slant="italic"), text_color="gray").pack(pady=(0, 15))

        f1 = ctk.CTkFrame(self, fg_color="transparent")
        f1.pack(pady=8)
        ctk.CTkLabel(f1, text="Username:", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
        self.username_entry = ctk.CTkEntry(f1, placeholder_text="Enter username...", width=200, height=35)
        self.username_entry.insert(0, "Player")
        self.username_entry.pack(side="left", padx=10)

        f2 = ctk.CTkFrame(self, fg_color="transparent")
        f2.pack(pady=8)
        ctk.CTkLabel(f2, text="Version:", font=ctk.CTkFont(size=14)).pack(side="left", padx=15)
        self.version_option = ctk.CTkOptionMenu(f2, values=["Fetching..."], width=200, height=35, fg_color="#52be80", button_color="#45b374", button_hover_color="#3da86a")
        self.version_option.pack(side="left", padx=10)

        self.ram_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.ram_frame.pack(pady=10, padx=20, fill="x")
        self.ram_label = ctk.CTkLabel(self.ram_frame, text="Allocated Memory: 2 GB", font=ctk.CTkFont(size=12, weight="bold"), text_color="#52be80")
        self.ram_label.pack()
        self.ram_slider = ctk.CTkSlider(self.ram_frame, from_=1, to=8, number_of_steps=7, command=self.update_ram_label, button_color="#45b374", button_hover_color="#3da86a", progress_color="#52be80")
        self.ram_slider.set(2)
        self.ram_slider.pack(pady=5)

        self.util_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.util_frame.pack(pady=10)
        self.folder_btn = ctk.CTkButton(self.util_frame, text="📁 Open Data Directory", font=ctk.CTkFont(size=11), width=150, height=30, fg_color="#34495e", hover_color="#2c3e50", command=lambda: os.startfile(GAME_DIR))
        self.folder_btn.pack(side="left", padx=10)
        
        self.theme_switch = ctk.CTkSwitch(self.util_frame, text="Dark Mode", font=ctk.CTkFont(size=11), command=self.toggle_theme, progress_color="#52be80")
        self.theme_switch.select()
        self.theme_switch.pack(side="left", padx=10)

        self.launch_button = ctk.CTkButton(self, text="LAUNCH MINECRAFT", font=ctk.CTkFont(size=14, weight="bold"), width=220, height=40, corner_radius=8, fg_color="#52be80", hover_color="#45b374", command=self.start_launch_thread)
        self.launch_button.pack(pady=(15, 10))

        self.status_label = ctk.CTkLabel(self, text="System Ready", font=ctk.CTkFont(size=12), text_color="#555555")
        self.status_label.pack()
        threading.Thread(target=self.load_versions, daemon=True).start()

    def update_ram_label(self, value):
        self.ram_label.configure(text=f"Allocated Memory: {int(value)} GB")

    def toggle_theme(self):
        ctk.set_appearance_mode("Dark" if self.theme_switch.get() == 1 else "Light")

    def load_web_icon(self):
        url = "https://raw.githubusercontent.com/Grassyboi/GrassyLauncher/refs/heads/main/GrassyLauncher.ico"
        if hasattr(sys, '_MEIPASS'):
            path = os.path.join(sys._MEIPASS, "GrassyLauncher.ico")
            if os.path.exists(path):
                try: 
                    self.iconbitmap(default=path)
                    return
                except: 
                    pass
        tmp = os.path.join(os.path.abspath(tempfile.gettempdir()), "temp_grassy_icon.ico")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as res:
                with open(tmp, "wb") as f: 
                    f.write(res.read())
            self.iconbitmap(default=tmp)
        except Exception: 
            pass

    def load_versions(self):
        fallbacks = ["26.2", "26.1", "1.20.1", "1.19.4", "1.16.5", "1.12.2", "1.8.9"]
        try:
            all_v = minecraft_launcher_lib.utils.get_version_list()
            rels = [v['id'] for v in all_v if v['type'] == 'release']
            try: 
                self.filtered_versions = rels[rels.index("26.2") : rels.index("1.8.9") + 1]
            except: 
                self.filtered_versions = fallbacks
        except: 
            self.filtered_versions = fallbacks
        self.after(0, self.update_version_menu)

    def update_version_menu(self):
        self.version_option.configure(values=self.filtered_versions)
        if self.filtered_versions: 
            self.version_option.set(self.filtered_versions[0])

    def update_status(self, text, color=None):
        self.status_label.configure(text=text)
        if color: 
            self.status_label.configure(text_color=color)

    def start_launch_thread(self):
        user = self.username_entry.get().strip()
        if not re.match(r"^[a-zA-Z0-9_]{3,16}$", user):
            messagebox.showerror("Invalid Profile Name", "Profile name must be 3 to 16 characters long and contain only letters, numbers, and underscores (_).")
            return
            
        ver = self.version_option.get()
        if ver == "Fetching...": 
            messagebox.showwarning("Warning", "Please wait for data profiles to load!")
            return
        
        self.toggle_ui_state("disabled")
        threading.Thread(target=self.launch_game, args=(user, ver), daemon=True).start()

    def toggle_ui_state(self, state):
        self.launch_button.configure(state=state)
        self.username_entry.configure(state=state)
        self.version_option.configure(state=state)
        self.ram_slider.configure(state=state)

    def launch_game(self, username, version):
        self.update_status("Preparing engine components...", "#52be80")
        cb = {"setStatus": lambda s: self.update_status(f"Fetching: {(s.split('/')[-1] if '/' in s else s)[:25]}...", "#e59866")}
        try:
            self.update_status("Evaluating core runtimes...", "#52be80")
            java_path = None
            try:
                minecraft_launcher_lib.runtime.install_jvm_runtime(version, GAME_DIR, callback=cb)
                java_path = minecraft_launcher_lib.runtime.get_executable_path(version, GAME_DIR)
            except: 
                pass
            
            self.update_status(f"Syncing environment build {version}...", "#e59866")
            minecraft_launcher_lib.install.install_minecraft_version(version, GAME_DIR, callback=cb)
            
            self.update_status("Applying execution optimizations...", "#52be80")
            optimize_game_settings()
            
            self.update_status("Booting Engine...", "#2ecc71")
            opts = {
                "username": username,
                "uuid": "00000000-0000-0000-0000-000000000000",
                "token": "0",
                "jvmArguments": [f"-Xmx{int(self.ram_slider.get())}G", "-Xms512M", "-Dminecraft.api.auth.host=localhost"]
            }
            
            if java_path and os.path.exists(java_path):
                try:
                    java_dir = os.path.dirname(java_path)
                    masked_exe = os.path.join(java_dir, "GameEngine.exe" if sys.platform == "win32" else "GameEngine")
                    if not os.path.exists(masked_exe):
                        shutil.copy2(java_path, masked_exe)
                    opts["executablePath"] = masked_exe
                except:
                    opts["executablePath"] = java_path

            cmd = minecraft_launcher_lib.command.get_minecraft_command(version, GAME_DIR, opts)
            
            self.after(0, self.withdraw)
            subprocess.run(cmd)
            self.after(0, self.deiconify)
            self.after(0, lambda: self.update_status("Runtime concluded.", "#2ecc71"))
        except Exception as e:
            err_msg = str(e)
            self.after(0, self.deiconify)
            self.after(0, lambda: self.update_status("Launch Interrupted", "#e74c3c"))
            self.after(0, lambda msg=err_msg: messagebox.showerror("Execution Failure", f"Failed to start core process:\n{msg}"))
        finally:
            self.after(0, lambda: self.toggle_ui_state("normal"))

if __name__ == "__main__":
    app = GrassyLauncher()
    app.mainloop()