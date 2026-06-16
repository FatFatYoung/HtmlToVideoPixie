import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import ctypes

# Language pack
LANG = {
    "en": {
        "title": "Html To Video Pixie v1.0.0",
        "subtitle": "AI Video Generation Tool",
        "install_dir": "Install Directory:",
        "browse": "Browse...",
        "desktop_shortcut": "Create Desktop Shortcut",
        "startmenu_shortcut": "Create Start Menu Shortcut",
        "ready": "Ready to install...",
        "install": "Install",
        "cancel": "Cancel",
        "copying": "Copying files...",
        "creating_desktop": "Creating desktop shortcut...",
        "creating_startmenu": "Creating start menu shortcut...",
        "completed": "Installation completed!",
        "success_msg": "Html To Video Pixie installed to:\n{path}",
        "run_title": "Run",
        "run_msg": "Run Html To Video Pixie now?",
        "error": "Error",
        "cannot_create": "Cannot create directory: {err}",
        "failed": "Installation failed: {err}",
        "select_dir": "Select Install Directory",
        "switch_lang": "简体中文",
    },
    "zh": {
        "title": "Html To Video Pixie v1.0.0",
        "subtitle": "AI智能视频生成工具",
        "install_dir": "安装目录：",
        "browse": "浏览...",
        "desktop_shortcut": "创建桌面快捷方式",
        "startmenu_shortcut": "创建开始菜单快捷方式",
        "ready": "准备安装...",
        "install": "安装",
        "cancel": "取消",
        "copying": "正在复制文件...",
        "creating_desktop": "正在创建桌面快捷方式...",
        "creating_startmenu": "正在创建开始菜单快捷方式...",
        "completed": "安装完成！",
        "success_msg": "Html To Video Pixie 已安装到：\n{path}",
        "run_title": "运行",
        "run_msg": "是否立即运行 Html To Video Pixie？",
        "error": "错误",
        "cannot_create": "无法创建目录：{err}",
        "failed": "安装失败：{err}",
        "select_dir": "选择安装目录",
        "switch_lang": "English",
    }
}

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

class Installer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Html To Video Pixie Installer")
        self.root.geometry("500x420")
        self.root.resizable(False, False)
        self.lang = "en"
        
        try:
            icon_path = Path(sys._MEIPASS) / "logo.ico" if getattr(sys, 'frozen', False) else Path(__file__).parent / "logo.ico"
            if icon_path.exists():
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        self.install_path = r"C:\Program Files\HtmlToVideoPixie"
        self.source_dir = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent
        
        self.create_widgets()
        
    def t(self, key):
        return LANG[self.lang].get(key, key)
        
    def create_widgets(self):
        # Language switch button
        top_bar = tk.Frame(self.root)
        top_bar.pack(fill="x", padx=10, pady=5)
        self.lang_btn = tk.Button(top_bar, text=self.t("switch_lang"), command=self.toggle_language)
        self.lang_btn.pack(side="right")
        
        # Title
        self.title_label = tk.Label(self.root, text=self.t("title"), font=("Arial", 16, "bold"))
        self.title_label.pack(pady=(10, 5))
        self.subtitle_label = tk.Label(self.root, text=self.t("subtitle"), font=("Arial", 10))
        self.subtitle_label.pack()
        
        # Install path
        self.dir_frame = tk.Frame(self.root)
        self.dir_frame.pack(fill="x", padx=40, pady=15)
        self.dir_label = tk.Label(self.dir_frame, text=self.t("install_dir"))
        self.dir_label.pack(anchor="w")
        
        path_frame = tk.Frame(self.dir_frame)
        path_frame.pack(fill="x", pady=5)
        self.path_var = tk.StringVar(value=self.install_path)
        tk.Entry(path_frame, textvariable=self.path_var, width=40).pack(side="left", fill="x", expand=True)
        self.browse_btn = tk.Button(path_frame, text=self.t("browse"), command=self.browse_path)
        self.browse_btn.pack(side="left", padx=5)
        
        # Options
        self.create_desktop = tk.BooleanVar(value=True)
        self.create_startmenu = tk.BooleanVar(value=True)
        self.desktop_cb = tk.Checkbutton(self.root, text=self.t("desktop_shortcut"), variable=self.create_desktop)
        self.desktop_cb.pack(anchor="w", padx=40)
        self.startmenu_cb = tk.Checkbutton(self.root, text=self.t("startmenu_shortcut"), variable=self.create_startmenu)
        self.startmenu_cb.pack(anchor="w", padx=40)
        
        # Progress
        self.progress_var = tk.StringVar(value=self.t("ready"))
        self.progress_label = tk.Label(self.root, textvariable=self.progress_var)
        self.progress_label.pack(pady=10)
        
        # Buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=15)
        self.install_btn = tk.Button(btn_frame, text=self.t("install"), command=self.install, width=15, height=2)
        self.install_btn.pack(side="left", padx=10)
        self.cancel_btn = tk.Button(btn_frame, text=self.t("cancel"), command=self.root.quit, width=15, height=2)
        self.cancel_btn.pack(side="left", padx=10)
        
    def toggle_language(self):
        self.lang = "zh" if self.lang == "en" else "en"
        self.update_ui()
        
    def update_ui(self):
        self.lang_btn.config(text=self.t("switch_lang"))
        self.title_label.config(text=self.t("title"))
        self.subtitle_label.config(text=self.t("subtitle"))
        self.dir_label.config(text=self.t("install_dir"))
        self.browse_btn.config(text=self.t("browse"))
        self.desktop_cb.config(text=self.t("desktop_shortcut"))
        self.startmenu_cb.config(text=self.t("startmenu_shortcut"))
        self.progress_var.set(self.t("ready"))
        self.install_btn.config(text=self.t("install"))
        self.cancel_btn.config(text=self.t("cancel"))
        
    def browse_path(self):
        path = filedialog.askdirectory(title=self.t("select_dir"))
        if path:
            self.path_var.set(os.path.join(path, "HtmlToVideoPixie"))
            
    def install(self):
        install_dir = self.path_var.get()
        try:
            os.makedirs(install_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror(self.t("error"), self.t("cannot_create").format(err=e))
            return
            
        files_to_copy = ["HtmlToVideoPixie.exe", "ffmpeg.exe", "logo.png", "logo.ico", "README.md", "LICENSE"]
        dirs_to_copy = ["config", "core"]
        
        try:
            self.progress_var.set(self.t("copying"))
            self.root.update()
            
            for f in files_to_copy:
                src = self.source_dir / f
                if src.exists():
                    shutil.copy2(src, install_dir)
                    
            for d in dirs_to_copy:
                src = self.source_dir / d
                if src.exists():
                    dst = Path(install_dir) / d
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                    
            os.makedirs(os.path.join(install_dir, "data"), exist_ok=True)
            os.makedirs(os.path.join(install_dir, "output"), exist_ok=True)
            os.makedirs(os.path.join(install_dir, "temp"), exist_ok=True)
            
            if self.create_desktop.get():
                self.progress_var.set(self.t("creating_desktop"))
                self.root.update()
                self.create_shortcut(install_dir, "desktop")
                
            if self.create_startmenu.get():
                self.progress_var.set(self.t("creating_startmenu"))
                self.root.update()
                self.create_shortcut(install_dir, "startmenu")
                
            self.progress_var.set(self.t("completed"))
            self.root.update()
            messagebox.showinfo(self.t("completed"), self.t("success_msg").format(path=install_dir))
            
            if messagebox.askyesno(self.t("run_title"), self.t("run_msg")):
                subprocess.Popen([os.path.join(install_dir, "HtmlToVideoPixie.exe")])
            self.root.quit()
            
        except Exception as e:
            messagebox.showerror(self.t("error"), self.t("failed").format(err=e))
            
    def create_shortcut(self, install_dir, location):
        exe_path = os.path.join(install_dir, "HtmlToVideoPixie.exe")
        icon_path = os.path.join(install_dir, "logo.ico")
        
        if location == "desktop":
            shortcut_path = os.path.join(os.path.expanduser("~"), "Desktop", "Html To Video Pixie.lnk")
        else:
            start_menu = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Html To Video Pixie")
            os.makedirs(start_menu, exist_ok=True)
            shortcut_path = os.path.join(start_menu, "Html To Video Pixie.lnk")
            
        ps_script = f'''
        $WshShell = New-Object -comObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
        $Shortcut.TargetPath = "{exe_path}"
        $Shortcut.WorkingDirectory = "{install_dir}"
        $Shortcut.IconLocation = "{icon_path}"
        $Shortcut.Description = "Html To Video Pixie - AI Video Generation Tool"
        $Shortcut.Save()
        '''
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    if not is_admin():
        run_as_admin()
    else:
        installer = Installer()
        installer.run()
