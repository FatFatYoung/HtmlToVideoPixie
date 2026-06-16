"""
视频生成模块 - 真正的HTML转视频
使用Playwright渲染HTML，FFmpeg合成视频
"""

import os
import sys
import json
import subprocess
import tempfile
import time
import re
import base64
from pathlib import Path
from typing import Optional, Tuple

# 检查Playwright
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# 检查PIL
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class VideoGenerator:
    """真正的HTML转视频生成器"""
    
    def __init__(self, output_dir: str = None, temp_dir: str = None):
        # 使用用户的应用数据目录
        app_data = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming')) / "HtmlToVideoPixie"
        
        if output_dir is None:
            self.output_dir = app_data / "output"
        else:
            self.output_dir = Path(output_dir)
            
        if temp_dir is None:
            self.temp_dir = app_data / "temp"
        else:
            self.temp_dir = Path(temp_dir)
            
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 检测FFmpeg
        self.ffmpeg_path = self._find_ffmpeg()
    
    def _find_ffmpeg(self) -> Optional[str]:
        """查找FFmpeg"""
        # 1. PyInstaller打包的临时目录
        if getattr(sys, 'frozen', False):
            temp_ffmpeg = Path(sys._MEIPASS) / "ffmpeg.exe"
            if temp_ffmpeg.exists():
                return str(temp_ffmpeg)
        
        # 2. EXE同目录
        exe_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent.parent
        local_ffmpeg = exe_dir / "ffmpeg.exe"
        if local_ffmpeg.exists():
            return str(local_ffmpeg)
        
        # 3. 检查PATH
        for cmd in ['ffmpeg', 'ffmpeg.exe']:
            try:
                result = subprocess.run(
                    [cmd, '-version'], 
                    capture_output=True, 
                    timeout=5,
                    shell=True
                )
                if result.returncode == 0:
                    return cmd
            except:
                pass
        
        # 4. 检查常见路径
        common_paths = [
            r'C:\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files\FFmpeg\bin\ffmpeg.exe',
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def generate_video_from_html(
        self, 
        html_content: str,
        output_filename: str = "animation.mp4",
        width: int = 800,
        height: int = 600,
        duration: int = 5,
        fps: int = 15,
        output_format: str = "mp4"
    ) -> Optional[str]:
        """
        从HTML生成真正的视频
        
        Args:
            html_content: HTML内容（支持CSS动画和JS）
            output_filename: 输出文件名
            width: 视频宽度
            height: 视频高度
            duration: 视频时长（秒）
            fps: 帧率
            output_format: 输出格式 (mp4 或 gif)
        
        Returns:
            输出文件路径，失败返回None
        """
        if not HAS_PLAYWRIGHT:
            print("错误：Playwright未安装，无法渲染HTML")
            return None
        
        try:
            # 1. 用Playwright渲染HTML并截图
            frames_dir = self.temp_dir / "frames"
            frames_dir.mkdir(exist_ok=True)
            
            # 清理旧帧
            for f in frames_dir.glob("*.png"):
                f.unlink()
            
            print(f"开始渲染HTML动画 ({duration}秒, {fps}fps)...")
            total_frames = duration * fps
            
            self._capture_frames_with_playwright(
                html_content, frames_dir, width, height, 
                total_frames, fps
            )
            
            # 2. 根据格式生成输出
            if output_format == "gif":
                return self._frames_to_gif(frames_dir, output_filename, fps)
            else:
                if not self.ffmpeg_path:
                    print("警告：FFmpeg未安装，将生成GIF代替")
                    return self._frames_to_gif(frames_dir, output_filename.replace('.mp4', '.gif'), fps)
                return self._frames_to_mp4(frames_dir, output_filename, fps)
                
        except Exception as e:
            print(f"生成失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _capture_frames_with_playwright(
        self, html_content: str, frames_dir: Path,
        width: int, height: int, total_frames: int, fps: int
    ):
        """使用Playwright捕获HTML动画帧"""
        # 保存HTML到临时文件
        html_file = self.temp_dir / "animation.html"
        html_file.write_text(html_content, encoding='utf-8')
        
        with sync_playwright() as p:
            # 尝试使用系统浏览器
            browser = None
            
            # Edge浏览器路径（Windows常见）
            edge_paths = [
                r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
            ]
            
            # Chrome浏览器路径
            chrome_paths = [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            ]
            
            # 尝试Edge
            for edge_path in edge_paths:
                if os.path.exists(edge_path):
                    try:
                        browser = p.chromium.launch(
                            headless=True,
                            executable_path=edge_path
                        )
                        print(f"使用Edge浏览器: {edge_path}")
                        break
                    except Exception as e:
                        print(f"尝试Edge {edge_path} 失败: {e}")
                        continue
            
            # 尝试Chrome
            if not browser:
                for chrome_path in chrome_paths:
                    if os.path.exists(chrome_path):
                        try:
                            browser = p.chromium.launch(
                                headless=True,
                                executable_path=chrome_path
                            )
                            print(f"使用Chrome: {chrome_path}")
                            break
                        except Exception as e:
                            print(f"尝试Chrome {chrome_path} 失败: {e}")
                            continue
            
            if not browser:
                # 尝试默认启动
                browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': width, 'height': height},
                device_scale_factor=1
            )
            page = context.new_page()
            
            # 加载HTML
            page.goto(f'file:///{html_file.absolute()}'.replace('\\', '/'))
            
            # 等待页面加载
            page.wait_for_load_state('networkidle')
            time.sleep(0.5)
            
            # 计算每帧间隔
            interval = 1.0 / fps
            
            # 捕获每一帧
            for i in range(total_frames):
                frame_path = frames_dir / f"frame_{i:05d}.png"
                page.screenshot(path=str(frame_path))
                
                # 等待到下一帧
                if i < total_frames - 1:
                    page.wait_for_timeout(int(interval * 1000))
                
                if (i + 1) % fps == 0:
                    print(f"  已渲染 {i + 1}/{total_frames} 帧 ({(i + 1) // fps}秒)")
            
            browser.close()
            print(f"帧捕获完成，共 {total_frames} 帧")
    
    def _frames_to_mp4(self, frames_dir: Path, output_filename: str, fps: int) -> Optional[str]:
        """用FFmpeg将帧序列合成MP4视频"""
        output_path = self.output_dir / output_filename
        try:
            cmd = [
                self.ffmpeg_path,
                '-y',
                '-framerate', str(fps),
                '-i', str(frames_dir / 'frame_%05d.png'),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', 'fast',
                '-crf', '23',
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=120,
                shell=True
            )
            
            if result.returncode == 0 and output_path.exists():
                print(f"MP4已生成: {output_path}")
                return str(output_path)
            else:
                print(f"FFmpeg错误: {result.stderr[-500:]}")
                return None
                
        except Exception as e:
            print(f"FFmpeg执行失败: {e}")
            return None
    
    def _frames_to_gif(self, frames_dir: Path, output_filename: str, fps: int) -> Optional[str]:
        """用FFmpeg将帧序列合成GIF"""
        output_path = self.output_dir / output_filename
        try:
            # 先生成调色板以提高GIF质量
            palette_path = self.temp_dir / "palette.png"
            cmd_palette = [
                self.ffmpeg_path,
                '-y',
                '-framerate', str(fps),
                '-i', str(frames_dir / 'frame_%05d.png'),
                '-vf', f'fps={fps},palettegen=stats_mode=diff',
                str(palette_path)
            ]
            
            subprocess.run(cmd_palette, capture_output=True, timeout=60, shell=True)
            
            # 用调色板生成GIF
            cmd_gif = [
                self.ffmpeg_path,
                '-y',
                '-framerate', str(fps),
                '-i', str(frames_dir / 'frame_%05d.png'),
                '-i', str(palette_path),
                '-lavfi', f'fps={fps} [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle',
                str(output_path)
            ]
            
            result = subprocess.run(cmd_gif, capture_output=True, text=True, timeout=120, shell=True)
            
            if result.returncode == 0 and output_path.exists():
                print(f"GIF已生成: {output_path}")
                return str(output_path)
            else:
                print(f"GIF生成失败: {result.stderr[-500:]}")
                return None
                
        except Exception as e:
            print(f"GIF生成失败: {e}")
            return None
    
    def _cleanup_frames(self, frames_dir: Path):
        """清理临时帧文件"""
        try:
            for f in frames_dir.glob("*.png"):
                f.unlink()
            frames_dir.rmdir()
        except:
            pass
    
    def get_status(self) -> dict:
        """获取生成器状态"""
        return {
            'playwright': HAS_PLAYWRIGHT,
            'pil': PIL_AVAILABLE,
            'ffmpeg': self.ffmpeg_path is not None,
            'ffmpeg_path': self.ffmpeg_path
        }