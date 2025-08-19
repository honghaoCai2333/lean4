import yaml
from typing import Optional, Dict, Any, Tuple
from .llm_client import LLMClient
from .lean_executor import LeanExecutor

class ProofProcessor:
    def __init__(self, config_path: str = "config/config.yaml", model: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.llm_client = LLMClient(config_path, model)
        self.lean_executor = LeanExecutor(self.config)
        self.max_attempts = self.config.get('lean', {}).get('max_attempts', 3)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}
    
    def _clean_lean_code(self, code: str) -> str:
        """
        清理生成的Lean代码，移除markdown标记等
        """
        # 移除markdown代码块标记
        lines = code.strip().split('\n')
        cleaned_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def process_proof(self, proof_statement: str) -> str:
        """
        处理证明请求的主要方法
        """
        result_parts = []
        result_parts.append(f"**输入的证明陈述:**\n{proof_statement}\n")
        
        # 检查Lean4是否安装
        if not self.lean_executor.check_lean_installation():
            result_parts.append("**警告:** Lean4未安装，将只生成证明代码而无法验证。")
            result_parts.append("请运行以下命令安装Lean4:")
            result_parts.append("```bash")
            result_parts.append("curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh")
            result_parts.append("source ~/.profile")
            result_parts.append("```\n")
        
        # 生成初始证明
        result_parts.append("**正在生成Lean4证明代码...**\n")
        try:
            lean_code = self.llm_client.generate_lean_proof(proof_statement)
            # 清理生成的代码
            lean_code = self._clean_lean_code(lean_code)
            result_parts.append("**生成的Lean4代码:**")
            result_parts.append("```lean")
            result_parts.append(lean_code)
            result_parts.append("```\n")
            
            # 如果Lean4已安装，尝试验证证明
            if self.lean_executor.check_lean_installation():
                success, verification_result = self._verify_and_refine_proof(lean_code)
                result_parts.append(verification_result)
            
            # 生成证明解释
            try:
                explanation = self.llm_client.explain_proof(lean_code)
                result_parts.append("**证明步骤解释:**")
                result_parts.append(explanation)
            except Exception as e:
                result_parts.append(f"**生成解释时出错:** {str(e)}")
                
        except Exception as e:
            result_parts.append(f"**生成证明时出错:** {str(e)}")
        
        return "\n".join(result_parts)
    
    def _verify_and_refine_proof(self, lean_code: str) -> Tuple[bool, str]:
        """
        验证并改进证明
        """
        result_parts = []
        current_code = lean_code
        
        for attempt in range(self.max_attempts):
            result_parts.append(f"**验证尝试 {attempt + 1}/{self.max_attempts}:**")
            
            # 验证当前代码
            is_valid, message = self.lean_executor.verify_proof(current_code)
            
            if is_valid:
                result_parts.append("✅ 证明验证成功!")
                if attempt > 0:
                    result_parts.append("\n**最终修正后的代码:**")
                    result_parts.append("```lean")
                    result_parts.append(current_code)
                    result_parts.append("```")
                return True, "\n".join(result_parts)
            else:
                result_parts.append(f"❌ 验证失败: {message}")
                
                # 如果不是最后一次尝试，则尝试修正
                if attempt < self.max_attempts - 1:
                    result_parts.append("正在尝试修正错误...")
                    try:
                        current_code = self.llm_client.refine_proof(current_code, message)
                        # 清理修正后的代码
                        current_code = self._clean_lean_code(current_code)
                        result_parts.append("已生成修正版本，继续验证...")
                    except Exception as e:
                        result_parts.append(f"修正过程中出错: {str(e)}")
                        break
        
        result_parts.append(f"\n❌ 经过{self.max_attempts}次尝试后仍无法验证证明")
        return False, "\n".join(result_parts)
    
    def validate_syntax_only(self, lean_code: str) -> Tuple[bool, str]:
        """
        仅进行语法验证
        """
        return self.lean_executor.verify_proof(lean_code)
    
    def get_proof_explanation(self, lean_code: str) -> str:
        """
        获取证明解释
        """
        return self.llm_client.explain_proof(lean_code)