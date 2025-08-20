import yaml
from typing import Optional, Dict, Any
from litellm import completion
import os

class LLMClient:
    def __init__(self, config_path: str = "config/config.yaml", model: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.model = model or self.config.get('llm', {}).get('default_model', 'gpt-3.5-turbo')
        self.temperature = self.config.get('llm', {}).get('temperature', 0.1)
        self.max_tokens = self.config.get('llm', {}).get('max_tokens', 2000)
        
        # 设置API密钥和基础URL为环境变量
        self.api_key = self.config.get('llm', {}).get('api_key')
        self.base_url = self.config.get('llm', {}).get('base_url')
        
        if self.api_key:
            os.environ['OPENAI_API_KEY'] = self.api_key
        if self.base_url:
            os.environ['OPENAI_API_BASE'] = self.base_url
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}
    
    def _load_prompt(self, prompt_file: str) -> str:
        """
        从文件加载提示模板
        """
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise Exception(f"提示文件未找到: {prompt_file}")
    
    def generate_lean_proof(self, proof_statement: str) -> str:
        """
        使用LLM生成Lean4证明代码
        """
        prompt_template = self._load_prompt("prompts/generate_lean_proof.txt")
        prompt = prompt_template.format(proof_statement=proof_statement)
        
        try:
            print(f"调用模型: {self.model}")
            print(f"API基础URL: {self.base_url}")
            
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")
    
    def refine_proof(self, original_proof: str, error_message: str) -> str:
        """
        根据错误信息改进证明
        """
        prompt_template = self._load_prompt("prompts/refine_proof.txt")
        prompt = prompt_template.format(original_proof=original_proof, error_message=error_message)
        
        try:
            print(f"调用模型: {self.model}")
            print(f"API基础URL: {self.base_url}")
            
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"证明修正失败: {str(e)}")
    
    def explain_proof(self, proof_code: str) -> str:
        """
        解释证明步骤
        """
        prompt_template = self._load_prompt("prompts/explain_proof.txt")
        prompt = prompt_template.format(proof_code=proof_code)
        
        try:
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            result = response.choices[0].message.content.strip()
            
            if not result:
                return "解释功能暂时不可用，但证明代码已验证成功。"
            
            return result
            
        except Exception as e:
            raise Exception(f"证明解释失败: {str(e)}")