"""
AI客户端模块
支持用户自定义服务商配置
"""

import os
import sys
import json
import time
import requests
from typing import Dict, List, Optional, Any
from pathlib import Path


class CustomAIClient:
    """自定义AI客户端"""
    
    def __init__(self, name: str, api_url: str, api_key: str, model_id: str):
        self.name = name
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.model_id = model_id
    
    def _get_endpoint(self):
        """自动拼接完整endpoint"""
        if self.api_url.endswith('/chat/completions'):
            return self.api_url
        return f"{self.api_url}/chat/completions"
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """发送聊天请求（非流式）"""
        result = ""
        for chunk in self.chat_stream(messages, **kwargs):
            result += chunk
        return result
    
    def chat_stream(self, messages: List[Dict[str, str]], **kwargs):
        """流式聊天请求，返回生成器"""
        endpoint = self._get_endpoint()
        
        # 认证头
        if "xiaomimimo.com" in self.api_url:
            headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        else:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        
        # 请求参数
        max_tokens_value = kwargs.get("max_tokens", None)
        data = {
            "model": self.model_id,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 1.0),
            "stream": True
        }
        if max_tokens_value is not None:
            if "xiaomimimo.com" in self.api_url:
                data["max_completion_tokens"] = max_tokens_value
            else:
                data["max_tokens"] = max_tokens_value
        
        print(f"\n[DEBUG] 流式API请求: {endpoint}, Model: {self.model_id}")
        
        # 带重试的请求
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=data,
                    timeout=(10, 300),
                    stream=True
                )
                
                print(f"[DEBUG] 响应状态: {response.status_code}")
                response.raise_for_status()
                
                # 解析SSE流
                for line in response.iter_lines():
                    if not line:
                        continue
                    line = line.decode('utf-8', errors='ignore')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            return
                        try:
                            chunk = json.loads(data_str)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                return
                
            except requests.exceptions.Timeout:
                last_error = f"请求超时 (尝试 {attempt + 1}/{max_retries})"
                print(f"[WARNING] {last_error}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                    
            except requests.exceptions.ConnectionError:
                last_error = f"连接失败 (尝试 {attempt + 1}/{max_retries})"
                print(f"[WARNING] {last_error}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                    
            except requests.exceptions.HTTPError as e:
                raise Exception(f"HTTP错误 {response.status_code}: {response.text[:200]}")
                
            except Exception as e:
                raise Exception(f"请求失败: {str(e)}")
        
        raise Exception(last_error or "请求失败")


class ProviderManager:
    """服务商配置管理器"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # 使用用户的应用数据目录
            app_data = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
            config_dir = app_data / "HtmlToVideoPixie"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / "providers.json"
        else:
            self.config_path = Path(config_path)
        self.providers = []
        self.default_provider_id = None
        self._load_config()
    
    def _load_config(self):
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.providers = config.get("providers", [])
                    self.default_provider_id = config.get("default_provider_id")
            else:
                # 如果用户目录没有配置，尝试从程序目录读取默认配置
                if getattr(sys, 'frozen', False):
                    default_config = Path(sys.executable).parent / "config" / "providers.json"
                else:
                    default_config = Path(__file__).parent.parent / "config" / "providers.json"
                if default_config.exists():
                    with open(default_config, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        self.providers = config.get("providers", [])
                        self.default_provider_id = config.get("default_provider_id")
                    self._save_config()  # 保存到用户目录
        except Exception as e:
            print(f"加载配置失败: {e}")
            self.providers = []
    
    def _save_config(self):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            config = {"providers": self.providers, "default_provider_id": self.default_provider_id}
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"[DEBUG] 配置已保存到: {self.config_path}")
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get_all_providers(self) -> List[Dict[str, Any]]:
        return self.providers
    
    def get_enabled_providers(self) -> List[Dict[str, Any]]:
        return [p for p in self.providers if p.get("enabled", True)]
    
    def get_provider_by_id(self, provider_id: str) -> Optional[Dict[str, Any]]:
        for p in self.providers:
            if p["id"] == provider_id:
                return p
        return None
    
    def get_provider_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        for p in self.providers:
            if p["name"] == name:
                return p
        return None
    
    def add_provider(self, name: str, api_url: str, api_key: str, model_id: str) -> str:
        provider_id = name.lower().replace(" ", "_")
        counter = 1
        original_id = provider_id
        while self.get_provider_by_id(provider_id):
            provider_id = f"{original_id}_{counter}"
            counter += 1
        
        provider = {
            "id": provider_id,
            "name": name,
            "api_url": api_url,
            "api_key": api_key,
            "model_id": model_id,
            "enabled": True
        }
        self.providers.append(provider)
        
        if len(self.providers) == 1:
            self.default_provider_id = provider_id
        
        self._save_config()
        return provider_id
    
    def update_provider(self, provider_id: str, **kwargs) -> bool:
        provider = self.get_provider_by_id(provider_id)
        if not provider:
            return False
        for key, value in kwargs.items():
            if key in ["name", "api_url", "api_key", "model_id", "enabled"]:
                provider[key] = value
        self._save_config()
        return True
    
    def delete_provider(self, provider_id: str) -> bool:
        provider = self.get_provider_by_id(provider_id)
        if not provider:
            return False
        self.providers.remove(provider)
        if self.default_provider_id == provider_id:
            self.default_provider_id = self.providers[0]["id"] if self.providers else None
        self._save_config()
        return True
    
    def set_default_provider(self, provider_id: str) -> bool:
        if not self.get_provider_by_id(provider_id):
            return False
        self.default_provider_id = provider_id
        self._save_config()
        return True
    
    def get_default_provider(self) -> Optional[Dict[str, Any]]:
        if self.default_provider_id:
            return self.get_provider_by_id(self.default_provider_id)
        elif self.providers:
            return self.providers[0]
        return None
    
    def create_client(self, provider_id: str = None) -> Optional[CustomAIClient]:
        if provider_id:
            provider = self.get_provider_by_id(provider_id)
        else:
            provider = self.get_default_provider()
        
        if not provider:
            return None
        
        return CustomAIClient(
            name=provider["name"],
            api_url=provider["api_url"],
            api_key=provider["api_key"],
            model_id=provider["model_id"]
        )