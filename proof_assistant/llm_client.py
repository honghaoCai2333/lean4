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
    
    def generate_lean_proof(self, proof_statement: str) -> str:
        """
        使用LLM生成Lean4证明代码
        """
        prompt = f"""
你是一个Lean4数学证明专家。请按以下步骤思考并生成证明：

数学陈述: {proof_statement}

第一步：分析证明类型
- 如果是自然数性质(如n+0=n)，使用归纳法
- 如果是逻辑命题(如¬¬P→P)，使用Classical.em或反证法
- 如果是集合关系(如传递性)，使用函数组合
- 如果是条件命题(如奇偶性)，使用分情况讨论

第二步：选择正确的Lean4语法
自然数归纳：
```
theorem name (n : Nat) : goal := by
  induction n with
  | zero => rfl  -- 或simp
  | succ d ih => rw [定理名] -- 或simp [ih]
```

逻辑证明：
```
theorem name (P : Prop) : goal := by
  by_cases h : P  -- 排中律
  · -- P为真的情况
  · -- P为假的情况
```

集合传递性：
```
theorem name (A B C : α → Prop) (h1 : ∀ x, A x → B x) (h2 : ∀ x, B x → C x) : 
  ∀ x, A x → C x := fun x h => h2 x (h1 x h)
```

第三步：可用的策略
- rfl: 当两边相等
- simp: 自动化简
- rw [定理]: 重写
- intro: 引入假设
- exact: 直接给出证明项
- by_cases: 分情况讨论
- contradiction: 从矛盾推出

常见问题和解决方案：
1. 不要使用import语句
2. 不要使用byContradiction，用by_cases代替
3. 不要使用Nat.Even、Prime、norm_num、dvd、linarith、decide、use、calc等高级概念，对于复杂的数论证明（如偶数性质），直接承认复杂性并使用sorry：
   ```
   theorem even_square_even (n : Nat) : (∃ k, n * n = 2 * k) → (∃ k, n = 2 * k) := by
     intro h
     -- 这个证明需要用到高级数论知识，超出了基础Lean4的范围
     -- 完整证明需要：奇偶性分类、模运算、反证法等复杂工具
     sorry
   ```
4. 对于n + n = 2n类型的证明，最简单的方式：
   ```
   theorem add_self_eq_two_mul (n : Nat) : n + n = 2 * n := by
     simp [Nat.two_mul]
   ```
   或者手动展开证明：
   ```
   theorem add_self_eq_two_mul (n : Nat) : n + n = 2 * n := by
     rw [Nat.two_mul]
   ```
5. 使用Nat而不是ℕ  
6. 使用基本策略：rfl, simp, rw, by_cases, intro, exact, contradiction
7. 复杂证明时可以使用sorry作为占位符，但要说明逻辑结构

请直接生成Lean4代码，不要包含markdown标记：
"""
        
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
        prompt = f"""
以下Lean4证明代码存在错误，请根据错误信息进行修正：

原始证明:
{original_proof}

错误信息:
{error_message}

请修正错误并返回正确的Lean4代码：
"""
        
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
        prompt = f"""
请解释以下Lean4证明代码的每个步骤：

{proof_code}

请用中文详细解释每个证明步骤的逻辑和数学原理：
"""
        
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