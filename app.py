#!/usr/bin/env python3

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import json
import yaml
from typing import Generator
from litellm import completion
import os
from proof_assistant import ProofProcessor
from proof_assistant.llm_client import LLMClient
from proof_assistant.lean_executor import LeanExecutor

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
        """流式生成证明过程"""
        try:
            # 1. 开始生成证明
            yield self._format_sse_message("开始生成Lean4证明代码...", "status")
            
            # 2. 使用完整的系统提示词
            system_prompt = self._load_prompt("prompts/system_prompt.txt")
            prompt = system_prompt.format(proof_statement=proof_statement)
            
            # 使用配置文件中的参数
            response = completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一名精通 Lean 4 与 mathlib 的数学家/形式化工程师。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,  # 使用配置文件中的值
                stream=True,
                timeout=60  # 超时设置为60秒
            )
            
            proof_code = ""
            yield self._format_sse_message("生成证明代码中：\n", "proof_start")
            
            chunk_count = 0
            for chunk in response:
                chunk_count += 1
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content = delta.content
                        proof_code += content
                        yield self._format_sse_message(content, "proof_chunk")
                
                # 每50个chunk发送一个心跳，保持连接活跃
                if chunk_count % 50 == 0:
                    yield self._format_sse_message("", "heartbeat")
            
            yield self._format_sse_message("", "proof_end")
            yield self._format_sse_message("✅ 证明生成完成", "success")
            yield self._format_sse_message("", "complete")
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error in stream_proof_generation: {error_msg}")  # 服务器端日志
            yield self._format_sse_message(f"错误: {error_msg}", "error")
            yield self._format_sse_message("", "complete")
    
    def _format_sse_message(self, content: str, message_type: str) -> str:
        """格式化SSE消息"""
        data = {
            "type": message_type,
            "content": content
        }
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

# 初始化处理器
processor = StreamingProofProcessor()

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

if __name__ == '__main__':
    app.run(debug=True, port=5001, threaded=True)