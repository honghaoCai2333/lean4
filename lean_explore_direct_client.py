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
                
                result = {
                    'id': item.id,
                    'title': item.primary_declaration.lean_name if item.primary_declaration else 'N/A',
                    'type': 'theorem',  # 默认类型
                    'description': item.informal_description or item.docstring or 'No description',
                    'statement': item.statement_text or item.display_statement_text or '',
                    'source_file': item.source_file,
                    'line': item.range_start_line,
                    'docstring': item.docstring
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
            
            return {
                'id': item.id,
                'name': item.primary_declaration.lean_name if item.primary_declaration else 'N/A',
                'statement': item.statement_text or item.display_statement_text or '',
                'docstring': item.docstring,
                'informal_description': item.informal_description,
                'source_file': item.source_file,
                'line': item.range_start_line
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