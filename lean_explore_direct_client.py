#!/usr/bin/env python3
"""
Direct LeanExplore API Client

直接使用 lean_explore.api.client 进行搜索，避免MCP的复杂性
"""

import asyncio
import sys
from typing import List, Dict, Any, Optional
import os
import yaml

# 导入 lean_explore 的 API 客户端
from lean_explore.api.client import Client as LeanExploreAPIClient
from lean_explore.cli.config_utils import load_api_key

class DirectLeanExploreClient:
    """直接的 LeanExplore API 客户端"""
    
    def __init__(self, config_path: str = "config/config.yaml", api_key: Optional[str] = None):
        self.config = self._load_config(config_path)
        
        # 优先级: 传入参数 > 项目配置文件 > lean-explore配置 > 环境变量
        self.api_key = (
            api_key or 
            self.config.get('lean_explore', {}).get('api_key') or
            load_api_key() or
            os.getenv('LEANEXPLORE_API_KEY')
        )
        
        if not self.api_key:
            raise ValueError("LeanExplore API key 未找到。请在配置文件、环境变量或参数中提供。")
        
        # 配置选项：是否截断长代码（默认不截断）
        self.truncate_output = self.config.get('lean_explore', {}).get('truncate_output', False)
        self.max_output_length = self.config.get('lean_explore', {}).get('max_output_length', 10000)
        
        # 初始化客户端
        self.client = LeanExploreAPIClient(api_key=self.api_key)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}
    
    async def search(self, query: str, limit: int = 10, package_filters: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        搜索数学知识和定理
        
        Args:
            query: 搜索查询字符串
            limit: 返回结果数量限制
            package_filters: 包过滤器列表
        
        Returns:
            搜索结果列表
        """
        try:
            response = await self.client.search(
                query=query, 
                package_filters=package_filters or []
            )
            
            # 转换为我们期望的格式
            results = []
            for i, item in enumerate(response.results):
                if i >= limit:
                    break
                
                # 确保完整输出，不截断长代码
                statement_text = item.statement_text or item.display_statement_text or ''
                docstring_text = item.docstring or ''
                description_text = item.informal_description or docstring_text or 'No description'
                
                # 如果配置了截断，才进行截断处理
                if self.truncate_output:
                    if len(statement_text) > self.max_output_length:
                        statement_text = statement_text[:self.max_output_length] + "... [输出被截断]"
                    if len(description_text) > self.max_output_length:
                        description_text = description_text[:self.max_output_length] + "... [输出被截断]"
                    if len(docstring_text) > self.max_output_length:
                        docstring_text = docstring_text[:self.max_output_length] + "... [输出被截断]"
                
                result = {
                    'id': item.id,
                    'title': item.primary_declaration.lean_name if item.primary_declaration else 'N/A',
                    'type': 'theorem',  # 默认类型
                    'description': description_text,
                    'statement': statement_text,
                    'source_file': item.source_file,
                    'line': item.range_start_line,
                    'docstring': docstring_text,
                    'full_content': True  # 标记这是完整内容，未被截断
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            raise RuntimeError(f"搜索失败: {e}")
    
    async def get_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取详细信息
        
        Args:
            item_id: 项目ID
        
        Returns:
            项目详细信息
        """
        try:
            item = await self.client.get_by_id(item_id)
            if not item:
                return None
            
            # 确保完整输出，不截断长代码
            statement_text = item.statement_text or item.display_statement_text or ''
            docstring_text = item.docstring or ''
            description_text = item.informal_description or ''
            
            # 如果配置了截断，才进行截断处理
            if self.truncate_output:
                if len(statement_text) > self.max_output_length:
                    statement_text = statement_text[:self.max_output_length] + "... [输出被截断]"
                if len(docstring_text) > self.max_output_length:
                    docstring_text = docstring_text[:self.max_output_length] + "... [输出被截断]"
                if len(description_text) > self.max_output_length:
                    description_text = description_text[:self.max_output_length] + "... [输出被截断]"
            
            return {
                'id': item.id,
                'name': item.primary_declaration.lean_name if item.primary_declaration else 'N/A',
                'statement': statement_text,
                'docstring': docstring_text,
                'informal_description': description_text,
                'source_file': item.source_file,
                'line': item.range_start_line,
                'full_content': True  # 标记这是完整内容，未被截断
            }
            
        except Exception as e:
            raise RuntimeError(f"获取详情失败: {e}")


async def main():
    """测试函数"""
    print("🔧 初始化直接 LeanExplore 客户端...")
    
    try:
        client = DirectLeanExploreClient()
        
        # 测试搜索
        print("🔍 搜索: 'The category of small categories has all small colimits'")
        results = await client.search("The category of small categories has all small colimits", limit=3)
        
        if results:
            print(f"✅ 找到 {len(results)} 个结果:\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']}")
                print(f"   ID: {result['id']}")
                print(f"   文件: {result['source_file']}:{result['line']}")
                print(f"   描述: {result['description']}")
                if result.get('statement'):
                    print(f"   陈述: {result['statement']}")
                print()
                
                # 获取第一个结果的详细信息
                if i == 1:
                    print(f"📖 获取详细信息 (ID: {result['id']}):")
                    details = await client.get_by_id(result['id'])
                    print("details: ", details)
                    print("==================================")
                    print("result: ", result)
                    # if details:
                    #     print(f"完整陈述: {details['statement']}")
                    #     if details['docstring']:
                    #         print(f"文档: {details['docstring']}")
                    print()
                break
        else:
            print("❌ 未找到相关结果")
        
        # 测试另一个搜索
        print("🔍 搜索: 'category theory colimit'")
        results2 = await client.search("category theory colimit", limit=2)
        
        if results2:
            print(f"✅ 找到 {len(results2)} 个结果:")
            for result in results2:
                print(f"- {result['title']} (ID: {result['id']})")
        
        print("\n✅ 测试完成!")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())