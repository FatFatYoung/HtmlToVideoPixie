#!/usr/bin/env python3
"""
Html To Video Pixie v1.0.0
AI智能视频生成工具 - 中英双语版
"""

import sys
import os
import json
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
import threading
import time
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from core.ai_client import ProviderManager
from core.i18n import t, lang


class DataManager:
    def __init__(self, data_dir=None):
        if data_dir is None:
            # 使用用户的应用数据目录
            app_data = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
            self.data_dir = app_data / "HtmlToVideoPixie"
        else:
            self.data_dir = Path(data_dir)
        self.creations_dir = self.data_dir / "creations"
        self.chats_dir = self.data_dir / "chats"
        self.creations_dir.mkdir(parents=True, exist_ok=True)
        self.chats_dir.mkdir(parents=True, exist_ok=True)

    def save_creation(self, html_content, user_input):
        now = datetime.now()
        ts = now.strftime("%Y%m%d_%H%M%S")
        title = user_input[:10]
        record = {"timestamp": ts, "date": now.strftime("%Y-%m-%d"),
                  "time": now.strftime("%H:%M:%S"), "title": title, "html": html_content}
        fp = self.creations_dir / f"{ts}.json"
        fp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')

    def get_creations(self):
        records = []
        for f in sorted(self.creations_dir.glob("*.json"), reverse=True):
            try:
                d = json.loads(f.read_text(encoding='utf-8'))
                d['filepath'] = str(f)
                records.append(d)
            except:
                pass
        return records

    def delete_creation(self, filepath):
        Path(filepath).unlink(missing_ok=True)

    def save_chat(self, chat_id, messages, title=None):
        if not title and messages:
            for m in messages:
                if m.get('role') == 'user':
                    title = m['content'][:10]
                    break
        record = {"chat_id": chat_id, "title": title or "Untitled",
                  "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "messages": messages}
        fp = self.chats_dir / f"{chat_id}.json"
        fp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')

    def get_chats(self):
        records = []
        for f in sorted(self.chats_dir.glob("*.json"), reverse=True):
            try:
                d = json.loads(f.read_text(encoding='utf-8'))
                d['filepath'] = str(f)
                records.append(d)
            except:
                pass
        return records

    def delete_chat(self, chat_id):
        fp = self.chats_dir / f"{chat_id}.json"
        fp.unlink(missing_ok=True)


class ChatPanel:
    def __init__(self, parent, dm):
        self.parent = parent
        self.dm = dm
        self.provider_manager = ProviderManager()
        self.conversation_history = []
        self.current_html = None
        self.current_chat_id = None
        self._streaming = False
        self._last_user_input = ""
        self.on_stream_start = None
        self.on_stream_update = None
        self.on_stream_done = None
        self.on_html_generated = None
        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self.parent)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Top bar with provider selection
        top = ttk.Frame(frame)
        top.pack(fill=tk.X, padx=5, pady=5)
        self.provider_label = ttk.Label(top, text=t("ai_provider"))
        self.provider_label.pack(side=tk.LEFT)
        self.provider_var = tk.StringVar()
        self.provider_combo = ttk.Combobox(top, textvariable=self.provider_var, state="readonly", width=15)
        self.provider_combo.pack(side=tk.LEFT, padx=5)
        self.model_label_text = ttk.Label(top, text=t("model") + " -")
        self.model_label_text.pack(side=tk.LEFT, padx=5)
        
        # Chat area
        self.chat_frame = ttk.LabelFrame(frame, text=t("dialog"), padding=5)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_text = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_text.pack(fill=tk.BOTH, expand=True)
        
        # Input area
        self.input_frame = ttk.LabelFrame(frame, text=t("input_hint"), padding=5)
        self.input_frame.pack(fill=tk.X, padx=5, pady=5)
        self.input_text = scrolledtext.ScrolledText(self.input_frame, wrap=tk.WORD, height=3)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        self.input_text.bind('<Return>', self._on_enter)
        self.input_text.bind('<Control-Return>', lambda e: None)
        self._refresh_providers()
        self._add_msg(t("welcome"))

    def update_language(self):
        """更新界面语言"""
        self.provider_label.config(text=t("ai_provider"))
        self.model_label_text.config(text=t("model") + " -")
        self.chat_frame.config(text=t("dialog"))
        self.input_frame.config(text=t("input_hint"))

    def _on_enter(self, event):
        if not (event.state & 0x4):
            self._send()
            return 'break'

    def _send(self):
        if self._streaming:
            return
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            return
        if not self.current_chat_id:
            self.current_chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._last_user_input = text
        self._add_msg(text, is_user=True)
        self.input_text.delete("1.0", tk.END)
        now = datetime.now()
        self.conversation_history.append({
            'role': 'user', 'content': text,
            'date': now.strftime("%Y-%m-%d"), 'time': now.strftime("%H:%M:%S")
        })
        self.input_text.config(state=tk.DISABLED)
        self._add_status(t("thinking"), "orange")
        self._streaming = True
        if self.on_stream_start:
            self.on_stream_start()

        def work():
            try:
                provider = self.provider_manager.get_provider_by_name(self.provider_var.get())
                if not provider:
                    raise Exception(t("select_provider"))
                from core.ai_client import CustomAIClient
                client = CustomAIClient(provider['name'], provider['api_url'], provider['api_key'], provider['model_id'])
                messages = [{"role": "system", "content": "Generate HTML animation code. Output HTML only, no explanations. Ensure code is complete."}]
                for msg in self.conversation_history[-5:]:
                    messages.append({"role": msg['role'], "content": msg['content']})
                self.parent.after(0, lambda: self._add_status(t("creating"), "blue"))
                full_response = ""
                for chunk in client.chat_stream(messages):
                    full_response += chunk
                    self.parent.after(0, lambda c=chunk: self._stream_update(c))
                self.parent.after(0, lambda r=full_response: self._stream_done(r))
            except Exception as e:
                self.parent.after(0, lambda msg=str(e): self._stream_error(msg))

        threading.Thread(target=work, daemon=True).start()

    def _add_status(self, text, color="black", show_load_btn=False):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, f"[{text}]", "status")
        if show_load_btn:
            self.chat_text.insert(tk.END, "  ")
            self.chat_text.insert(tk.END, f"[{t('load_html')}]", "load_link")
            self.chat_text.tag_config("load_link", foreground="blue", underline=True, font=("Arial", 10))
            self.chat_text.tag_bind("load_link", "<Button-1>", lambda e: self._load_to_editor())
        self.chat_text.insert(tk.END, "\n\n")
        self.chat_text.tag_config("status", foreground=color, font=("Arial", 10, "italic"))
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

    def _stream_update(self, chunk):
        if self.on_stream_update:
            self.on_stream_update(chunk)

    def _stream_done(self, full_response):
        html = self._extract_html(full_response)
        if html:
            self.current_html = html
            self.dm.save_creation(html, self._last_user_input)
        self._add_status(t("completed"), "green", show_load_btn=bool(html))
        now = datetime.now()
        self.conversation_history.append({
            'role': 'assistant', 'content': full_response, 'html': html or '',
            'date': now.strftime("%Y-%m-%d"), 'time': now.strftime("%H:%M:%S")
        })
        self.dm.save_chat(self.current_chat_id, self.conversation_history)
        self.input_text.config(state=tk.NORMAL)
        self._streaming = False
        if self.on_stream_done:
            self.on_stream_done()
        # Auto-popup video settings dialog
        if html and self.on_html_generated:
            self.on_html_generated(html)
            self.parent.after(500, lambda: self._show_video_settings(html))

    def _stream_error(self, error):
        self._add_status(f"{t('error')}: {error[:50]}", "red")
        self.input_text.config(state=tk.NORMAL)
        self._streaming = False
        if self.on_stream_done:
            self.on_stream_done()

    def _load_to_editor(self):
        if self.current_html and self.on_html_generated:
            self.on_html_generated(self.current_html)

    def _show_video_settings(self, html):
        """Show video settings dialog"""
        VideoSettingsDialog(self.parent, html)

    def _extract_html(self, text):
        if not text:
            return None
        text = str(text)
        if '```html' in text:
            s = text.find('```html') + 7
            e = text.find('```', s)
            if e != -1:
                return text[s:e].strip()
        for marker in ['<!DOCTYPE html>', '<!doctype html>', '<html']:
            i = text.find(marker)
            if i != -1:
                for em in ['</html>', '</HTML>']:
                    j = text.rfind(em)
                    if j != -1:
                        return text[i:j + len(em)]
        return None

    def _add_msg(self, msg, is_user=False):
        self.chat_text.config(state=tk.NORMAL)
        tag = "user" if is_user else "ai"
        prefix = f"{t('you')}: " if is_user else f"{t('ai')}: "
        self.chat_text.insert(tk.END, prefix, tag)
        self.chat_text.insert(tk.END, msg + "\n\n")
        self.chat_text.tag_config("user", foreground="blue", font=("Arial", 10, "bold"))
        self.chat_text.tag_config("ai", foreground="green", font=("Arial", 10, "bold"))
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

    def _refresh_providers(self):
        providers = self.provider_manager.get_enabled_providers()
        self.provider_combo['values'] = [p["name"] for p in providers]
        default = self.provider_manager.get_default_provider()
        if default:
            self.provider_var.set(default["name"])
            p = self.provider_manager.get_provider_by_name(default["name"])
            if p:
                self.model_label_text.config(text=f"{t('model')} {p.get('model_id', '-')}")

    def refresh_providers(self):
        self._refresh_providers()

    def new_chat(self):
        if self.conversation_history:
            self.dm.save_chat(self.current_chat_id, self.conversation_history)
        self.conversation_history = []
        self.current_chat_id = None
        self.current_html = None
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)
        self.chat_text.config(state=tk.DISABLED)
        self._add_msg(t("new_chat_started"))

    def load_chat(self, chat_data):
        self.current_chat_id = chat_data.get('chat_id')
        self.conversation_history = chat_data.get('messages', [])
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)
        for msg in self.conversation_history:
            if msg['role'] == 'user':
                self._add_msg(msg['content'], is_user=True)
            else:
                if msg.get('html'):
                    self.current_html = msg['html']
                    self._add_status_with_html(t("completed"), "green", msg['html'])
                else:
                    content = msg['content'].replace('```html', '').replace('```', '').strip()
                    self._add_msg(content[:200] + "..." if len(content) > 200 else content)
        self._add_status(t("chat_loaded"), "blue")

    def _add_status_with_html(self, text, color, html):
        """显示状态+绑定特定HTML的加载按钮"""
        tag_name = f"load_{id(html)}"
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, f"[{text}]", "status")
        self.chat_text.insert(tk.END, "  ")
        self.chat_text.insert(tk.END, f"[{t('load_html')}]", tag_name)
        self.chat_text.insert(tk.END, "\n\n")
        self.chat_text.tag_config("status", foreground=color, font=("Arial", 10, "italic"))
        self.chat_text.tag_config(tag_name, foreground="blue", underline=True, font=("Arial", 10))
        self.chat_text.tag_bind(tag_name, "<Button-1>", lambda e, h=html: self.on_html_generated(h) if self.on_html_generated else None)
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)


class EditorPanel:
    def __init__(self, parent):
        self.parent = parent
        self.current_html = None
        self._streaming = False
        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.parent)
        main.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar
        self.toolbar = ttk.Frame(main)
        self.toolbar.pack(fill=tk.X, padx=5, pady=5)
        self.apply_btn = ttk.Button(self.toolbar, text=t("apply"), command=self._apply)
        self.apply_btn.pack(side=tk.LEFT, padx=2)
        self.format_btn = ttk.Button(self.toolbar, text=t("format"), command=self._format)
        self.format_btn.pack(side=tk.LEFT, padx=2)
        self.reset_btn = ttk.Button(self.toolbar, text=t("reset"), command=self._reset)
        self.reset_btn.pack(side=tk.LEFT, padx=2)
        self.browser_btn = ttk.Button(self.toolbar, text=t("browser_open"), command=self._open_in_browser)
        self.browser_btn.pack(side=tk.LEFT, padx=2)
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        self.gen_btn = ttk.Button(self.toolbar, text=t("generate_video"), command=self._show_video_settings)
        self.gen_btn.pack(side=tk.LEFT, padx=5)
        
        # Editor area
        self.editor_frame = ttk.LabelFrame(main, text=t("html_code"), padding=5)
        self.editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        editor = ttk.Frame(self.editor_frame)
        editor.pack(fill=tk.BOTH, expand=True)
        self.line_nums = tk.Text(editor, width=4, padx=3, takefocus=0, border=0, background='#f0f0f0', state='disabled', font=("Consolas", 10))
        self.line_nums.pack(side=tk.LEFT, fill=tk.Y)
        self.code_text = scrolledtext.ScrolledText(editor, wrap=tk.NONE, font=("Consolas", 10))
        self.code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.code_text.bind('<KeyRelease>', self._update_lines)
        
        # Status bar
        self.status = ttk.Label(main, text=t("ready"), foreground="gray")
        self.status.pack(fill=tk.X, padx=5, pady=2)

    def update_language(self):
        """更新界面语言"""
        self.apply_btn.config(text=t("apply"))
        self.format_btn.config(text=t("format"))
        self.reset_btn.config(text=t("reset"))
        self.browser_btn.config(text=t("browser_open"))
        self.gen_btn.config(text=t("generate_video"))
        self.editor_frame.config(text=t("html_code"))
        self.status.config(text=t("ready"))

    def load_html(self, html):
        self.current_html = html
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert("1.0", html)
        self._update_lines()
        self.status.config(text=f"{t('loaded_html')} ({len(html)} chars)")

    def stream_start(self):
        self._streaming = True
        self.code_text.delete("1.0", tk.END)
        self.status.config(text=t("ai_creating"))

    def stream_update(self, chunk):
        if self._streaming:
            chunk = chunk.replace('```html', '').replace('```', '')
            if chunk:
                self.code_text.insert(tk.END, chunk)
                self.code_text.see(tk.END)

    def stream_done(self):
        self._streaming = False
        content = self.code_text.get("1.0", tk.END).strip()
        if content:
            self.current_html = content
            self._update_lines()
            self.status.config(text=f"{t('created')} ({len(content)} chars)")

    def _update_lines(self, event=None):
        self.line_nums.config(state='normal')
        self.line_nums.delete('1.0', tk.END)
        count = self.code_text.get('1.0', tk.END).count('\n')
        self.line_nums.insert('1.0', '\n'.join(str(i) for i in range(1, count + 1)))
        self.line_nums.config(state='disabled')

    def _apply(self):
        code = self.code_text.get("1.0", tk.END).strip()
        if code:
            self.current_html = code
            messagebox.showinfo(t("success"), t("applied"))

    def _format(self):
        code = self.code_text.get("1.0", tk.END).strip()
        if not code:
            return
        result = []
        indent = 0
        for token in re.split(r'(</?[^>]+>)', code):
            token = token.strip()
            if not token:
                continue
            if token.startswith('</'):
                indent = max(0, indent - 1)
                result.append("  " * indent + token)
            elif token.startswith('<') and not token.endswith('/>'):
                result.append("  " * indent + token)
                if not any(t in token.lower() for t in ['<br', '<hr', '<img', '<input', '<meta', '<link']):
                    indent += 1
            else:
                result.append("  " * indent + token)
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert("1.0", '\n'.join(result))
        self._update_lines()

    def _reset(self):
        if self.current_html:
            self.code_text.delete("1.0", tk.END)
            self.code_text.insert("1.0", self.current_html)
            self._update_lines()

    def _open_in_browser(self):
        if not self.current_html:
            messagebox.showwarning(t("warning"), t("no_html"))
            return
        import webbrowser
        # 使用用户目录下的temp目录
        app_data = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
        temp_dir = app_data / "HtmlToVideoPixie" / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = temp_dir / "preview.html"
        temp_file.write_text(self.current_html, encoding='utf-8')
        webbrowser.open(str(temp_file.absolute()))

    def _show_video_settings(self):
        if not self.current_html:
            messagebox.showwarning(t("warning"), t("no_html"))
            return
        VideoSettingsDialog(self.parent, self.current_html)


class VideoSettingsDialog:
    def __init__(self, parent, html_content):
        self.html_content = html_content
        self.parent = parent
        self.win = tk.Toplevel(parent)
        self.win.title(t("video_settings"))
        self.win.geometry("400x320")
        self.win.resizable(False, False)
        # 不使用 grab_set 和 transient，避免最小化问题
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build()

    def _on_close(self):
        self.win.destroy()

    def _build(self):
        main = ttk.Frame(self.win, padding=20)
        main.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main, text=t("video_settings"), font=("Arial", 12, "bold")).pack(pady=(0, 15))

        settings = ttk.Frame(main)
        settings.pack(fill=tk.X)

        ttk.Label(settings, text=t("output_format")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.format_var = tk.StringVar(value="mp4")
        ff = ttk.Frame(settings)
        ff.grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=10, pady=5)
        ttk.Radiobutton(ff, text=t("mp4_video"), variable=self.format_var, value="mp4").pack(side=tk.LEFT)
        ttk.Radiobutton(ff, text=t("gif_image"), variable=self.format_var, value="gif").pack(side=tk.LEFT, padx=10)

        ttk.Label(settings, text=t("width")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.w_var = tk.StringVar(value="800")
        ttk.Entry(settings, textvariable=self.w_var, width=10).grid(row=1, column=1, padx=10, pady=5)
        ttk.Label(settings, text=t("height")).grid(row=1, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.h_var = tk.StringVar(value="600")
        ttk.Entry(settings, textvariable=self.h_var, width=10).grid(row=1, column=3, padx=10, pady=5)

        ttk.Label(settings, text=t("duration")).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.dur_var = tk.StringVar(value="5")
        ttk.Entry(settings, textvariable=self.dur_var, width=10).grid(row=2, column=1, padx=10, pady=5)
        ttk.Label(settings, text=t("fps")).grid(row=2, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.fps_var = tk.StringVar(value="10")
        ttk.Entry(settings, textvariable=self.fps_var, width=10).grid(row=2, column=3, padx=10, pady=5)

        self.status = ttk.Label(main, text=t("ready"), foreground="gray")
        self.status.pack(pady=10)
        btns = ttk.Frame(main)
        btns.pack(fill=tk.X, pady=10)
        self.gen_btn = ttk.Button(btns, text=t("confirm_generate"), command=self._generate)
        self.gen_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text=t("cancel"), command=self.win.destroy).pack(side=tk.LEFT, padx=5)

    def _generate(self):
        self.gen_btn.config(state=tk.DISABLED, text=t("generating"))
        self.status.config(text=t("generating_video"), foreground="blue")

        def work():
            try:
                from core.video_generator import VideoGenerator
                gen = VideoGenerator()
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                fmt = self.format_var.get()
                filename = f"{ts}.{fmt}"
                path = gen.generate_video_from_html(
                    self.html_content, output_filename=filename,
                    width=int(self.w_var.get()), height=int(self.h_var.get()),
                    duration=int(self.dur_var.get()), fps=int(self.fps_var.get()),
                    output_format=fmt)
                self.win.after(0, lambda: self._done(path))
            except Exception as e:
                self.win.after(0, lambda: self._error(str(e)))

        threading.Thread(target=work, daemon=True).start()

    def _done(self, path):
        self.gen_btn.config(state=tk.NORMAL, text=t("confirm_generate"))
        if path:
            self.status.config(text=t("generate_success"), foreground="green")
            messagebox.showinfo(t("success"), f"{t('generated')}\n{path}")
            self.win.destroy()
            os.startfile(str(Path(path).parent))
        else:
            self.status.config(text=t("generate_failed"), foreground="red")
            messagebox.showerror(t("error"), t("generate_failed"))

    def _error(self, err):
        self.gen_btn.config(state=tk.NORMAL, text=t("confirm_generate"))
        self.status.config(text=t("error"), foreground="red")
        messagebox.showerror(t("error"), f"{t('generate_failed')}:\n{err}")


class MainWindow:
    def __init__(self):
        self.dm = DataManager()
        self.root = tk.Tk()
        self.root.title("Html To Video Pixie")
        self.root.geometry("1200x800")
        self.root.report_callback_exception = self._on_exception
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 设置图标
        try:
            icon_path = Path(__file__).parent / "logo.ico"
            if icon_path.exists():
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        self._build_ui()

    def _on_exception(self, exc_type, exc_value, exc_tb):
        import traceback
        print(f"[ERROR] {''.join(traceback.format_exception(exc_type, exc_value, exc_tb))}")
        messagebox.showerror(t("error"), str(exc_value))

    def _build_ui(self):
        # Top bar with language switch
        top_bar = ttk.Frame(self.root)
        top_bar.pack(fill=tk.X, padx=5, pady=2)
        
        # Language switch button on the right
        self.lang_btn = ttk.Button(top_bar, text=t("switch_lang"), command=self._toggle_language)
        self.lang_btn.pack(side=tk.RIGHT, padx=5)
        
        # Menu bar
        self._build_menu()
        
        # Main content
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        left = ttk.Frame(paned)
        paned.add(left, weight=1)
        self.chat_panel = ChatPanel(left, self.dm)
        right = ttk.Frame(paned)
        paned.add(right, weight=2)
        self.editor_panel = EditorPanel(right)
        self.chat_panel.on_stream_start = self.editor_panel.stream_start
        self.chat_panel.on_stream_update = self.editor_panel.stream_update
        self.chat_panel.on_stream_done = self.editor_panel.stream_done
        self.chat_panel.on_html_generated = self.editor_panel.load_html

    def _build_menu(self):
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # Operation menu
        self.op_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=t("menu.operation"), menu=self.op_menu)
        self.op_menu.add_command(label=t("menu.new_chat"), command=self._new_chat)
        self.op_menu.add_command(label=t("menu.import_html"), command=self._import_html)
        self.op_menu.add_command(label=t("menu.creations"), command=self._show_creations)
        self.op_menu.add_command(label=t("menu.chat_management"), command=self._show_chats)
        self.op_menu.add_separator()
        self.op_menu.add_command(label=t("menu.exit"), command=self.root.quit)

        self.menubar.add_command(label=t("menu.model_settings"), command=self._show_providers)
        self.menubar.add_command(label=t("menu.about"), command=self._about)

    def _toggle_language(self):
        """切换语言"""
        lang.toggle_language()
        self.lang_btn.config(text=t("switch_lang"))
        self._rebuild_menu()
        self.chat_panel.update_language()
        self.editor_panel.update_language()

    def _rebuild_menu(self):
        """重建菜单"""
        self.menubar.delete(0, tk.END)
        
        self.op_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=t("menu.operation"), menu=self.op_menu)
        self.op_menu.add_command(label=t("menu.new_chat"), command=self._new_chat)
        self.op_menu.add_command(label=t("menu.import_html"), command=self._import_html)
        self.op_menu.add_command(label=t("menu.creations"), command=self._show_creations)
        self.op_menu.add_command(label=t("menu.chat_management"), command=self._show_chats)
        self.op_menu.add_separator()
        self.op_menu.add_command(label=t("menu.exit"), command=self.root.quit)

        self.menubar.add_command(label=t("menu.model_settings"), command=self._show_providers)
        self.menubar.add_command(label=t("menu.about"), command=self._about)

    def _new_chat(self):
        self.chat_panel.new_chat()

    def _import_html(self):
        file_path = filedialog.askopenfilename(
            title="Select HTML file" if lang.get_language() == "en" else "选择HTML文件",
            filetypes=[("HTML files", "*.html;*.htm"), ("All files", "*.*")]
        )
        if file_path:
            try:
                content = Path(file_path).read_text(encoding='utf-8')
                self.editor_panel.load_html(content)
            except Exception as e:
                messagebox.showerror(t("error"), f"{t('read_failed')} {e}")

    def _show_creations(self):
        win = tk.Toplevel(self.root)
        win.title(t("creations_title"))
        win.geometry("700x450")
        win.transient(self.root)
        win.grab_set()

        canvas = tk.Canvas(win)
        scrollbar = ttk.Scrollbar(win, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        records = self.dm.get_creations()
        if not records:
            ttk.Label(scroll_frame, text=t("no_creations")).pack(pady=20)
        else:
            for r in records:
                row = ttk.Frame(scroll_frame)
                row.pack(fill=tk.X, pady=2)
                ttk.Label(row, text=f"{r['date']} {r['time']}", width=20).pack(side=tk.LEFT)
                ttk.Label(row, text=r['title'], width=30).pack(side=tk.LEFT, padx=5)
                fp = r['filepath']
                html = r['html']
                ttk.Button(row, text=t("load"), command=lambda h=html: self.editor_panel.load_html(h)).pack(side=tk.LEFT, padx=2)
                ttk.Button(row, text=t("delete"), command=lambda f=fp, rw=row: self._delete_creation(f, rw)).pack(side=tk.LEFT, padx=2)

    def _delete_creation(self, filepath, row):
        if messagebox.askyesno(t("confirm"), t("confirm_delete")):
            self.dm.delete_creation(filepath)
            row.destroy()

    def _show_chats(self):
        win = tk.Toplevel(self.root)
        win.title(t("chats_title"))
        win.geometry("700x450")
        win.transient(self.root)
        win.grab_set()

        canvas = tk.Canvas(win)
        scrollbar = ttk.Scrollbar(win, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        chats = self.dm.get_chats()
        if not chats:
            ttk.Label(scroll_frame, text=t("no_chats")).pack(pady=20)
        else:
            for c in chats:
                row = ttk.Frame(scroll_frame)
                row.pack(fill=tk.X, pady=2)
                ttk.Label(row, text=c['created_at'], width=18).pack(side=tk.LEFT)
                ttk.Label(row, text=c['title'], width=30).pack(side=tk.LEFT, padx=5)
                cid = c['chat_id']
                data = c
                ttk.Button(row, text=t("load_chat"), command=lambda d=data: (self.chat_panel.load_chat(d), win.destroy())).pack(side=tk.LEFT, padx=2)
                ttk.Button(row, text=t("delete"), command=lambda id=cid, rw=row: self._delete_chat(id, rw)).pack(side=tk.LEFT, padx=2)

    def _delete_chat(self, chat_id, row):
        if messagebox.askyesno(t("confirm"), t("confirm_delete_chat")):
            self.dm.delete_chat(chat_id)
            row.destroy()

    def _about(self):
        w = tk.Toplevel(self.root)
        w.title(t("about_title"))
        w.geometry("400x250")
        w.resizable(False, False)
        w.configure(bg="white")
        
        tk.Label(w, text="Html To Video Pixie", font=("Arial", 14, "bold"), bg="white").pack(pady=(20, 5))
        tk.Label(w, text=t("version"), bg="white").pack()
        tk.Label(w, text=t("description"), justify=tk.CENTER, bg="white").pack(pady=10)
        tk.Label(w, text=t("author"), bg="white").pack(pady=(0, 5))
        link = tk.Label(w, text="https://github.com/FatFatYoung/HtmlToVideoPixie", 
                       fg="blue", cursor="hand2", bg="white")
        link.pack(pady=(0, 20))
        link.bind("<Button-1>", lambda e: __import__('webbrowser').open("https://github.com/FatFatYoung/HtmlToVideoPixie"))

    def _show_providers(self):
        win = tk.Toplevel(self.root)
        win.title(t("provider_settings"))
        win.geometry("700x400")
        win.resizable(False, False)
        # 不使用 grab_set 和 transient，避免最小化问题
        pm = ProviderManager()
        main = ttk.Frame(win, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main, text=t("provider_settings"), font=("Arial", 12, "bold")).pack(pady=(0, 10))
        list_frame = ttk.LabelFrame(main, text=t("provider_list"), padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True)
        tree = ttk.Treeview(list_frame, columns=("name", "url", "model", "status"), show="headings", height=8)
        tree.heading("name", text=t("name"))
        tree.heading("url", text=t("api_url"))
        tree.heading("model", text=t("model_id"))
        tree.heading("status", text=t("status"))
        sb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        def refresh():
            for i in tree.get_children():
                tree.delete(i)
            for p in pm.get_all_providers():
                tree.insert("", tk.END, iid=p["id"], values=(p["name"], p["api_url"], p["model_id"], t("enabled") if p.get("enabled", True) else t("disabled")))
            self.chat_panel.refresh_providers()

        refresh()
        
        # 窗口关闭时刷新
        def on_close():
            self.chat_panel.refresh_providers()
            win.destroy()
        
        win.protocol("WM_DELETE_WINDOW", on_close)
        
        btns = ttk.Frame(main)
        btns.pack(fill=tk.X, pady=10)

        def add():
            self._provider_dialog(win, pm, None, refresh)

        def edit():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning(t("warning"), t("select_provider"))
                return
            self._provider_dialog(win, pm, sel[0], refresh)

        def delete():
            sel = tree.selection()
            if not sel:
                return
            p = pm.get_provider_by_id(sel[0])
            if messagebox.askyesno(t("confirm"), f"Delete {p['name']}?" if lang.get_language() == "en" else f"删除 {p['name']}？"):
                pm.delete_provider(sel[0])
                refresh()

        ttk.Button(btns, text=t("add"), command=add).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text=t("edit"), command=edit).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text=t("delete"), command=delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(btns, text=t("close"), command=win.destroy).pack(side=tk.LEFT, padx=2)

    def _provider_dialog(self, parent, pm, pid, refresh):
        win = tk.Toplevel(parent)
        win.title(t("add_provider") if not pid else t("edit_provider"))
        win.geometry("450x300")
        win.resizable(False, False)
        # 不使用 grab_set 和 transient，避免最小化问题
        p = pm.get_provider_by_id(pid) if pid else None
        f = ttk.Frame(win, padding=20)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text=t("name") + ":").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value=p["name"] if p else "")
        ttk.Entry(f, textvariable=name_var, width=35).grid(row=0, column=1, pady=5)
        ttk.Label(f, text=t("api_url") + ":").grid(row=1, column=0, sticky=tk.W, pady=5)
        url_var = tk.StringVar(value=p["api_url"] if p else "")
        ttk.Entry(f, textvariable=url_var, width=35).grid(row=1, column=1, pady=5)
        ttk.Label(f, text=t("api_key") + ":").grid(row=2, column=0, sticky=tk.W, pady=5)
        key_var = tk.StringVar(value=p["api_key"] if p else "")
        ttk.Entry(f, textvariable=key_var, show="*", width=35).grid(row=2, column=1, pady=5)
        ttk.Label(f, text=t("model_id") + ":").grid(row=3, column=0, sticky=tk.W, pady=5)
        model_var = tk.StringVar(value=p["model_id"] if p else "")
        ttk.Entry(f, textvariable=model_var, width=35).grid(row=3, column=1, pady=5)
        f.columnconfigure(1, weight=1)
        btns = ttk.Frame(win)
        btns.pack(fill=tk.X, padx=20, pady=20)

        def save():
            n, u, k, m = name_var.get().strip(), url_var.get().strip(), key_var.get().strip(), model_var.get().strip()
            if not all([n, u, k, m]):
                messagebox.showwarning(t("warning"), t("fill_all"))
                return
            if pid:
                pm.update_provider(pid, name=n, api_url=u, api_key=k, model_id=m)
            else:
                pm.add_provider(n, u, k, m)
            refresh()
            win.destroy()

        def test():
            u, k, m = url_var.get().strip(), key_var.get().strip(), model_var.get().strip()
            if not all([u, k, m]):
                messagebox.showwarning(t("warning"), t("fill_api"))
                return
            try:
                from core.ai_client import CustomAIClient
                c = CustomAIClient("test", u, k, m)
                c.chat([{"role": "user", "content": "Hi"}], max_tokens=10)
                messagebox.showinfo(t("success"), t("connection_success"))
            except Exception as e:
                messagebox.showerror(t("failed"), str(e))

        ttk.Button(btns, text=t("save"), command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text=t("test"), command=test).pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text=t("cancel"), command=win.destroy).pack(side=tk.LEFT, padx=5)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    import traceback
    def show_error(exc_type, exc_value, exc_tb):
        print(f"[ERROR] {''.join(traceback.format_exception(exc_type, exc_value, exc_tb))}")
        try:
            messagebox.showerror(t("error"), str(exc_value))
        except:
            pass
    tk.Tk.report_callback_exception = show_error
    app = MainWindow()
    app.run()

