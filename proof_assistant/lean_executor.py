import subprocess
import tempfile
import os
from pathlib import Path
from typing import Tuple, Optional

class LeanExecutor:
    def __init__(self, config: dict):
        self.timeout = config.get('lean', {}).get('timeout', 30)
        self.max_attempts = config.get('lean', {}).get('max_attempts', 3)
        
    def check_lean_installation(self) -> bool:
        """
        检查Lean4是否正确安装
        """
        try:
            result = subprocess.run(['lean', '--version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def verify_proof(self, lean_code: str) -> Tuple[bool, str]:
        """
        验证Lean4证明代码
        返回: (是否成功, 输出信息或错误信息)
        """
        if not self.check_lean_installation():
            return False, "错误: Lean4未安装或无法访问。请先安装Lean4。"
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lean', delete=False) as f:
            f.write(lean_code)
            temp_file = f.name
        
        try:
            # 运行lean检查
            result = subprocess.run(
                ['lean', temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                return True, "证明验证成功！"
            else:
                return False, result.stderr or result.stdout
                
        except subprocess.TimeoutExpired:
            return False, f"证明验证超时（超过{self.timeout}秒）"
        except Exception as e:
            return False, f"验证过程中发生错误: {str(e)}"
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def create_lean_project(self, project_name: str) -> bool:
        """
        创建新的Lean4项目
        """
        try:
            result = subprocess.run(
                ['lake', 'new', project_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def build_lean_project(self, project_path: str) -> Tuple[bool, str]:
        """
        构建Lean4项目
        """
        try:
            result = subprocess.run(
                ['lake', 'build'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                return True, "项目构建成功"
            else:
                return False, result.stderr or result.stdout
                
        except subprocess.TimeoutExpired:
            return False, "项目构建超时"
        except Exception as e:
            return False, f"构建过程中发生错误: {str(e)}"
    
    def format_lean_code(self, lean_code: str) -> str:
        """
        格式化Lean4代码（基础版本）
        """
        lines = lean_code.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append('')
                continue
                
            # 简单的缩进逻辑
            if any(keyword in stripped for keyword in ['theorem', 'lemma', 'def', 'structure', 'inductive']):
                formatted_lines.append('  ' * indent_level + stripped)
                if ':=' in stripped or 'by' in stripped:
                    indent_level += 1
            elif stripped in ['by', 'where']:
                formatted_lines.append('  ' * indent_level + stripped)
                indent_level += 1
            elif stripped.startswith('·') or stripped.startswith('sorry'):
                formatted_lines.append('  ' * indent_level + stripped)
            else:
                formatted_lines.append('  ' * indent_level + stripped)
        
        return '\n'.join(formatted_lines)