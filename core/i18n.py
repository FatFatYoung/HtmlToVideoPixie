"""
国际化模块 - 中英文双语支持
"""

# 语言包
TRANSLATIONS = {
    "zh": {
        # 菜单
        "menu.operation": "操作",
        "menu.new_chat": "新对话",
        "menu.import_html": "导入HTML",
        "menu.creations": "创作记录",
        "menu.chat_management": "对话管理",
        "menu.exit": "退出",
        "menu.model_settings": "模型设置",
        "menu.about": "关于",
        
        # ChatPanel
        "ai_provider": "AI服务商:",
        "model": "模型:",
        "dialog": "对话",
        "input_hint": "输入 (Enter发送, Ctrl+Enter换行)",
        "welcome": "欢迎！请输入动画需求",
        "thinking": "思考中...",
        "creating": "创作中...",
        "completed": "已完成创作",
        "load_html": "加载HTML代码",
        "new_chat_started": "新对话已开始，请输入动画需求",
        "chat_loaded": "对话已加载",
        "you": "你",
        "ai": "AI",
        
        # EditorPanel
        "apply": "应用更改",
        "format": "格式化",
        "reset": "重置",
        "browser_open": "浏览器打开",
        "generate_video": "生成视频",
        "html_code": "HTML代码",
        "ready": "就绪",
        "applied": "已应用更改",
        "no_html": "没有HTML内容",
        "ai_creating": "AI创作中...",
        "created": "创作完成",
        "loaded_html": "已加载HTML",
        
        # VideoSettingsDialog
        "video_settings": "视频生成设置",
        "output_format": "输出格式:",
        "mp4_video": "MP4视频",
        "gif_image": "GIF动图",
        "width": "宽度:",
        "height": "高度:",
        "duration": "时长(秒):",
        "fps": "帧率:",
        "confirm_generate": "确认生成",
        "cancel": "取消",
        "generating": "生成中...",
        "generating_video": "正在生成...",
        "generate_success": "生成完成！",
        "generate_failed": "生成失败",
        "generated": "已生成:",
        
        # Creations
        "creations_title": "创作记录",
        "no_creations": "暂无创作记录",
        "load": "加载HTML",
        "delete": "删除",
        "confirm_delete": "删除该记录？",
        
        # Chats
        "chats_title": "对话管理",
        "no_chats": "暂无对话记录",
        "load_chat": "加载对话",
        "confirm_delete_chat": "删除该对话？",
        
        # Provider Settings
        "provider_settings": "模型设置",
        "provider_list": "服务商列表",
        "name": "名称",
        "api_url": "API地址",
        "model_id": "模型",
        "status": "状态",
        "enabled": "启用",
        "disabled": "禁用",
        "add": "添加",
        "edit": "编辑",
        "close": "关闭",
        "add_provider": "添加服务商",
        "edit_provider": "编辑服务商",
        "api_key": "API密钥:",
        "save": "保存",
        "test": "测试",
        "select_provider": "请选择服务商",
        "fill_all": "请填写所有字段",
        "fill_api": "请先填写API地址、密钥和模型",
        "connection_success": "连接成功！",
        "connection_failed": "失败",
        
        # About
        "about_title": "关于",
        "version": "v1.0.0",
        "description": "输入视频需求，大模型生成 HTML 动画，\n内置引擎渲染成视频/动图。\n单 EXE，无需安装环境。就这么简单。",
        "author": "作者：FatFatYoung",
        
        # General
        "success": "成功",
        "error": "错误",
        "warning": "提示",
        "confirm": "确认",
        "failed": "失败",
        "read_failed": "读取失败:",
        
        # Language switch
        "switch_lang": "English",
    },
    "en": {
        # Menu
        "menu.operation": "Operation",
        "menu.new_chat": "New Chat",
        "menu.import_html": "Import HTML",
        "menu.creations": "Creations",
        "menu.chat_management": "Chat History",
        "menu.exit": "Exit",
        "menu.model_settings": "Model Settings",
        "menu.about": "About",
        
        # ChatPanel
        "ai_provider": "AI Provider:",
        "model": "Model:",
        "dialog": "Dialog",
        "input_hint": "Input (Enter to send, Ctrl+Enter for new line)",
        "welcome": "Welcome! Please describe your animation needs",
        "thinking": "Thinking...",
        "creating": "Creating...",
        "completed": "Creation completed",
        "load_html": "Load HTML Code",
        "new_chat_started": "New chat started, please describe your animation needs",
        "chat_loaded": "Chat loaded",
        "you": "You",
        "ai": "AI",
        
        # EditorPanel
        "apply": "Apply Changes",
        "format": "Format",
        "reset": "Reset",
        "browser_open": "Open in Browser",
        "generate_video": "Generate Video",
        "html_code": "HTML Code",
        "ready": "Ready",
        "applied": "Changes applied",
        "no_html": "No HTML content",
        "ai_creating": "AI creating...",
        "created": "Creation completed",
        "loaded_html": "HTML loaded",
        
        # VideoSettingsDialog
        "video_settings": "Video Generation Settings",
        "output_format": "Output Format:",
        "mp4_video": "MP4 Video",
        "gif_image": "GIF Image",
        "width": "Width:",
        "height": "Height:",
        "duration": "Duration (sec):",
        "fps": "FPS:",
        "confirm_generate": "Generate",
        "cancel": "Cancel",
        "generating": "Generating...",
        "generating_video": "Generating video...",
        "generate_success": "Generation completed!",
        "generate_failed": "Generation failed",
        "generated": "Generated:",
        
        # Creations
        "creations_title": "Creations",
        "no_creations": "No creations yet",
        "load": "Load HTML",
        "delete": "Delete",
        "confirm_delete": "Delete this record?",
        
        # Chats
        "chats_title": "Chat History",
        "no_chats": "No chat history",
        "load_chat": "Load Chat",
        "confirm_delete_chat": "Delete this chat?",
        
        # Provider Settings
        "provider_settings": "Model Settings",
        "provider_list": "Provider List",
        "name": "Name",
        "api_url": "API URL",
        "model_id": "Model",
        "status": "Status",
        "enabled": "Enabled",
        "disabled": "Disabled",
        "add": "Add",
        "edit": "Edit",
        "close": "Close",
        "add_provider": "Add Provider",
        "edit_provider": "Edit Provider",
        "api_key": "API Key:",
        "save": "Save",
        "test": "Test",
        "select_provider": "Please select a provider",
        "fill_all": "Please fill in all fields",
        "fill_api": "Please fill in API URL, Key and Model first",
        "connection_success": "Connection successful!",
        "connection_failed": "Failed",
        
        # About
        "about_title": "About",
        "version": "v1.0.0",
        "description": "Describe your video needs, AI generates HTML animation,\nbuilt-in engine renders to video/GIF.\nSingle EXE, no environment needed. Simple as that.",
        "author": "Author: FatFatYoung",
        
        # General
        "success": "Success",
        "error": "Error",
        "warning": "Warning",
        "confirm": "Confirm",
        "failed": "Failed",
        "read_failed": "Read failed:",
        
        # Language switch
        "switch_lang": "简体中文",
    }
}


class LanguageManager:
    """语言管理器"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.current_lang = "en"  # 默认英文
        return cls._instance
    
    def get(self, key: str) -> str:
        """获取翻译文本"""
        return TRANSLATIONS.get(self.current_lang, TRANSLATIONS["en"]).get(key, key)
    
    def set_language(self, lang: str):
        """设置语言"""
        if lang in TRANSLATIONS:
            self.current_lang = lang
    
    def get_language(self) -> str:
        """获取当前语言"""
        return self.current_lang
    
    def toggle_language(self):
        """切换语言"""
        self.current_lang = "zh" if self.current_lang == "en" else "en"
        return self.current_lang


# 全局实例
lang = LanguageManager()


def t(key: str) -> str:
    """翻译快捷函数"""
    return lang.get(key)
