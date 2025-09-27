#!/usr/bin/env python3

from flask import Flask, request, jsonify, Response, stream_with_context, send_from_directory
from flask_cors import CORS
import json
import yaml
from typing import Generator
from litellm import completion
import os
from proof_assistant import ProofProcessor
from proof_assistant.llm_client import LLMClient
from proof_assistant.lean_executor import LeanExecutor
from database import ProofDatabase
from lean_explore_direct_client import DirectLeanExploreClient

app = Flask(__name__)
CORS(app)

class StreamingProofProcessor:
    def __init__(self, config_path: str = "config/config.yaml", model: str = None):
        self.config = self._load_config(config_path)
        self.model = model or self.config.get('llm', {}).get('default_model', 'gpt-3.5-turbo')
        self.temperature = self.config.get('llm', {}).get('temperature', 0.1)
        self.max_tokens = self.config.get('llm', {}).get('max_tokens', 2000)
        self.lean_executor = LeanExecutor(self.config)
        
        # 设置API密钥和基础URL
        self.api_key = self.config.get('llm', {}).get('api_key')
        self.base_url = self.config.get('llm', {}).get('base_url')
        
        if self.api_key:
            os.environ['OPENAI_API_KEY'] = self.api_key
        if self.base_url:
            os.environ['OPENAI_API_BASE'] = self.base_url
            
        # 添加SSL相关环境变量，尝试解决SSL问题
        import ssl
        import certifi
        os.environ['SSL_CERT_FILE'] = certifi.where()
        os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    
    def _load_config(self, config_path: str) -> dict:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}
    
    def _load_prompt(self, prompt_file: str) -> str:
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise Exception(f"提示文件未找到: {prompt_file}")
    
    def stream_proof_generation(self, proof_statement: str) -> Generator:
        """生成证明过程"""
        try:
            # 1. 开始生成证明
            yield self._format_sse_message("开始生成Lean4证明代码...", "status")
            
            # 2. 先搜索lean-explore相关知识
            search_context = ""
            if lean_explore_available:
                try:
                    yield self._format_sse_message("🔍 正在搜索相关的数学知识...", "status")
                    
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    search_results = loop.run_until_complete(
                        lean_explore.search(proof_statement, limit=3)
                    )
                    
                    if search_results:
                        knowledge_content = "## 相关数学知识\n\n"
                        knowledge_content += "Lean代码和相关Mathlib定理：\n\n"
                        
                        # 只显示第一个结果的完整信息
                        if len(search_results) > 0:
                            result = search_results[0]
                            knowledge_content += f"### {result['title']}\n"
                            knowledge_content += f"**文件位置**: `{result['source_file']}:{result['line']}`\n\n"
                            if result.get('statement'):
                                knowledge_content += f"**Lean代码**:\n```lean\n{result['statement']}\n```\n\n"
                            if result.get('description'):
                                knowledge_content += f"**说明**: {result['description']}\n\n"
                        
                        # 输出搜索结果供用户查看
                        yield self._format_sse_message(knowledge_content, "knowledge_chunk")
                        
                        # 为LLM准备上下文信息
                        search_context = f"\n\n相关数学知识和定理：\n{knowledge_content}"
                    
                    loop.close()
                    
                except Exception as e:
                    print(f"LeanExplore搜索失败: {e}")
                    yield self._format_sse_message(f"🔍 知识搜索遇到问题，继续生成证明...", "status")
            
            # 3. 使用完整的系统提示词并结合搜索结果
            system_prompt = self._load_prompt("prompts/system_prompt.txt")
            prompt = system_prompt.format(proof_statement=proof_statement)
            
            # 将搜索结果添加到用户提示中
            enhanced_prompt = prompt + search_context
            
            # # 添加调试信息
            # print(f"Using model: {self.model}")
            # print(f"API base URL: {self.base_url}")
            # print(f"Temperature: {self.temperature}")
            
            yield self._format_sse_message("正在连接AI服务...", "status")
            
            # 使用litellm的非流式请求
            response = completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一名精通 Lean 4 与 mathlib 的数学家/形式化工程师。"},
                    {"role": "user", "content": enhanced_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=False,  # 非流式请求
                timeout=300
            )
            
            yield self._format_sse_message("AI正在生成证明...", "proof_start")
            
            # 获取完整响应
            if hasattr(response, 'choices') and len(response.choices) > 0:
                content = response.choices[0].message.content
                
                # 模拟流式输出效果
                import time
                words = content.split()
                current_content = ""
                
                # 按句子分割，避免重复
                sentences = content.replace('\n\n', '|PARAGRAPH|').replace('\n', ' ').split('。')
                current_chunk = ""
                
                for sentence in sentences:
                    if sentence.strip():
                        sentence = sentence.replace('|PARAGRAPH|', '\n\n').strip()
                        current_chunk += sentence + "。"
                        
                        # 当积累到合适长度或遇到段落分隔时输出
                        if len(current_chunk) > 200 or '|PARAGRAPH|' in sentence:
                            yield self._format_sse_message(current_chunk, "proof_chunk")
                            current_chunk = ""
                            time.sleep(0.3)
                
                # 输出最后的内容
                if current_chunk:
                    yield self._format_sse_message(current_chunk, "proof_chunk")
                    time.sleep(0.3)
                
                yield self._format_sse_message("", "proof_end")
                
                # 添加 Lean 验证步骤
                if self.lean_executor.check_lean_installation():
                    yield self._format_sse_message("🔧 开始验证生成的 Lean 代码...", "status")
                    
                    # 提取并清理 Lean 代码
                    lean_code = self._clean_lean_code(content)
                    
                    if lean_code.strip():
                        # 进行流式验证
                        verification_gen = self._verify_and_refine_proof_streaming(lean_code)
                        for verification_message in verification_gen:
                            yield verification_message
                    else:
                        yield self._format_sse_message("⚠️ 未能从生成的内容中提取有效的 Lean 代码", "warning")
                else:
                    yield self._format_sse_message("⚠️ Lean4 未安装，跳过代码验证", "warning")
            
            yield self._format_sse_message("证明生成完成", "success")
            yield self._format_sse_message("", "complete")
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            traceback_msg = traceback.format_exc()
            print(f"Error in stream_proof_generation: {error_msg}")
            print(f"Full traceback: {traceback_msg}")
            yield self._format_sse_message(f"错误: {error_msg}", "error")
            yield self._format_sse_message("", "complete")
    
    def _clean_lean_code(self, code: str) -> str:
        """清理生成的Lean代码，移除markdown标记等"""
        lines = code.strip().split('\n')
        cleaned_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _verify_and_refine_proof_streaming(self, lean_code: str) -> Generator:
        """流式验证并改进证明"""
        max_attempts = self.config.get('lean', {}).get('max_attempts', 3)
        current_code = lean_code
        
        for attempt in range(max_attempts):
            yield self._format_sse_message(f"🔍 验证尝试 {attempt + 1}/{max_attempts}...", "status")
            
            # 验证当前代码
            is_valid, message = self.lean_executor.verify_proof(current_code)
            
            if is_valid:
                yield self._format_sse_message("✅ 证明验证成功!", "verification_success")
                if attempt > 0:
                    yield self._format_sse_message("**最终修正后的代码:**", "status")
                    yield self._format_sse_message(f"```lean\n{current_code}\n```", "refined_code")
                return True
            else:
                yield self._format_sse_message(f"❌ 验证失败: {message}", "verification_error")
                
                # 如果不是最后一次尝试，则尝试修正
                if attempt < max_attempts - 1:
                    yield self._format_sse_message("🔧 正在尝试修正错误...", "status")
                    try:
                        # 这里需要添加LLM修正功能，目前先跳过
                        yield self._format_sse_message("修正功能待实现，跳过自动修正", "status")
                        break
                    except Exception as e:
                        yield self._format_sse_message(f"修正过程中出错: {str(e)}", "error")
                        break
        
        yield self._format_sse_message(f"❌ 经过{max_attempts}次尝试后仍无法验证证明", "verification_failed")
        return False

    def _format_sse_message(self, content: str, message_type: str) -> str:
        """格式化SSE消息"""
        data = {
            "type": message_type,
            "content": content
        }
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

# 初始化处理器、数据库和LeanExplore客户端
processor = StreamingProofProcessor()
db = ProofDatabase()
try:
    lean_explore = DirectLeanExploreClient()
    lean_explore_available = True
except Exception as e:
    print(f"LeanExplore客户端初始化失败: {e}")
    lean_explore = None
    lean_explore_available = False

@app.route('/api/prove', methods=['POST'])
def prove():
    """证明API接口，支持流式输出"""
    try:
        data = request.json
        proof_statement = data.get('statement')
        
        if not proof_statement:
            return jsonify({"error": "请提供需要证明的命题"}), 400
        
        # 返回流式响应
        return Response(
            stream_with_context(processor.stream_proof_generation(proof_statement)),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """健康检查接口"""
    return jsonify({"status": "healthy"})

@app.route('/api/test', methods=['POST'])
def test_api():
    """测试API连接"""
    try:
        response = completion(
            model=processor.model,
            messages=[{"role": "user", "content": "Hello, test connection"}],
            max_tokens=10,
            timeout=30
        )
        return jsonify({"status": "success", "response": str(response)})
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error", 
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """获取历史会话列表"""
    try:
        sessions = db.get_recent_sessions(limit=3)  # 只返回最近3个
        return jsonify({"sessions": sessions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """创建新会话"""
    try:
        data = request.json
        statement = data.get('statement')
        title = data.get('title')
        is_static = data.get('isStatic', False)
        static_content = data.get('staticContent', '')
        
        if not statement:
            return jsonify({"error": "请提供需要证明的命题"}), 400
        
        session_id = db.create_session(statement, title)
        
        # 如果是静态内容，直接保存证明结果
        if is_static and static_content:
            # 将静态内容转换为与真实API相同的格式
            formatted_content = processor._format_sse_message(static_content, "proof_chunk")
            db.update_session_proof(session_id, formatted_content)
        
        session = db.get_session(session_id)
        return jsonify({"session": session}), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    """获取特定会话详情"""
    try:
        session = db.get_session(session_id)
        if not session:
            return jsonify({"error": "会话不存在"}), 404
        return jsonify({"session": session})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sessions/<int:session_id>/prove', methods=['POST'])
def prove_in_session(session_id):
    """在特定会话中进行证明"""
    try:
        # 检查会话是否存在
        session = db.get_session(session_id)
        if not session:
            return jsonify({"error": "会话不存在"}), 404
        
        # 使用会话中的statement进行证明
        statement = session['statement']
        
        # 保存完整的证明结果
        full_proof = ""
        
        def generate_and_save():
            nonlocal full_proof
            
            # 直接调用stream_proof_generation，它现在已经包含了搜索功能
            for chunk in processor.stream_proof_generation(statement):
                full_proof += chunk
                yield chunk
            
            # 证明完成后保存到数据库
            db.update_session_proof(session_id, full_proof)
        
        # 返回流式响应
        return Response(
            stream_with_context(generate_and_save()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_lean_explore():
    """LeanExplore搜索接口"""
    try:
        data = request.json
        query = data.get('query')
        limit = data.get('limit', 5)
        
        if not query:
            return jsonify({"error": "请提供搜索查询"}), 400
        
        if not lean_explore_available:
            return jsonify({"error": "LeanExplore服务不可用"}), 503
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(
                lean_explore.search(query, limit=limit)
            )
            
            return jsonify({
                "query": query,
                "results": results,
                "count": len(results)
            })
            
        finally:
            loop.close()
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search/<int:theorem_id>', methods=['GET'])
def get_theorem_details(theorem_id):
    """获取定理详细信息"""
    try:
        if not lean_explore_available:
            return jsonify({"error": "LeanExplore服务不可用"}), 503
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            details = loop.run_until_complete(
                lean_explore.get_by_id(theorem_id)
            )
            
            if not details:
                return jsonify({"error": "定理不存在"}), 404
                
            return jsonify({"theorem": details})
            
        finally:
            loop.close()
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    """提供前端HTML文件"""
    return send_from_directory('front', 'chat.html')

@app.route('/<path:filename>')
def static_files(filename):
    """提供静态文件"""
    return send_from_directory('front', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5001, threaded=True)