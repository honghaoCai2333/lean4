import asyncio
import json
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import yaml
import subprocess
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPLeanExploreClient:
    """
    MCP LeanExplore 客户端
    通过 Model Context Protocol 连接到 LeanExplore 服务器
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.session: Optional[ClientSession] = None
        self.server_params = None
        self._setup_server_params()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f"配置文件 {config_path} 未找到，使用默认配置")
            return {}
    
    def _setup_server_params(self):
        """设置 MCP 服务器参数"""
        # 从配置获取 LeanExplore MCP 服务器信息
        lean_explore_config = self.config.get('lean_explore', {})
        api_key = lean_explore_config.get('api_key')
        
        if not api_key:
            raise ValueError("LeanExplore API key 未在配置文件中设置")
        
        # 设置环境变量
        os.environ['LEAN_EXPLORE_API_KEY'] = api_key
        
        # 配置 MCP 服务器参数
        server_command = lean_explore_config.get('server_command', '/path/to/your/leanexplore/package')
        server_args = lean_explore_config.get('server_args', [
            'mcp', 'serve', '--backend', 'api', '--api-key', api_key
        ])
        
        # 确保 args 中的 API key 是最新的
        if isinstance(server_args, list):
            # 替换 args 中的 API key
            processed_args = []
            for arg in server_args:
                if arg == "YOUR_ACTUAL_LEANEXPLORE_API_KEY":
                    processed_args.append(api_key)
                else:
                    processed_args.append(arg)
            server_args = processed_args
        
        self.server_params = StdioServerParameters(
            command=server_command,
            args=server_args,
            env={
                "LEAN_EXPLORE_API_KEY": api_key,
                "PATH": os.environ.get("PATH", "")
            }
        )
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()
    
    async def connect(self):
        """连接到 MCP 服务器"""
        try:
            # 创建 stdio 客户端连接
            async with stdio_client(self.server_params) as (read_stream, write_stream):
                self.session = ClientSession(read_stream, write_stream)
                
                # 初始化会话
                await self.session.initialize()
                
                logger.info("成功连接到 LeanExplore MCP 服务器")
            
        except Exception as e:
            logger.error(f"连接 MCP 服务器失败: {e}")
            raise ConnectionError(f"无法连接到 LeanExplore MCP 服务器: {e}")
    
    async def disconnect(self):
        """断开 MCP 连接"""
        if self.session:
            try:
                await self.session.close()
                logger.info("已断开 MCP 连接")
            except Exception as e:
                logger.error(f"断开连接时出错: {e}")
    
    async def search(self, query: str, limit: int = 10, search_type: str = 'all') -> List[Dict[str, Any]]:
        """
        搜索数学知识和定理
        
        Args:
            query: 搜索查询字符串
            limit: 返回结果数量限制
            search_type: 搜索类型 ('all', 'theorems', 'definitions', 'lemmas')
        
        Returns:
            搜索结果列表
        """
        if not self.session:
            raise RuntimeError("MCP 客户端未连接，请先调用 connect()")
        
        try:
            # 调用 MCP 服务器的 search 工具
            result = await self.session.call_tool(
                "search",
                arguments={
                    "query": query,
                    "limit": limit,
                    "type": search_type
                }
            )
            
            # 解析结果
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return json.loads(content.text)
                elif hasattr(content, 'data'):
                    return content.data
            
            return []
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            raise RuntimeError(f"搜索操作失败: {e}")
    
    async def get_theorem_details(self, theorem_id: str) -> Dict[str, Any]:
        """
        获取定理详细信息
        
        Args:
            theorem_id: 定理ID
        
        Returns:
            定理详细信息
        """
        if not self.session:
            raise RuntimeError("MCP 客户端未连接，请先调用 connect()")
        
        try:
            result = await self.session.call_tool(
                "get_theorem",
                arguments={"theorem_id": theorem_id}
            )
            
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return json.loads(content.text)
                elif hasattr(content, 'data'):
                    return content.data
            
            return {}
            
        except Exception as e:
            logger.error(f"获取定理详情失败: {e}")
            raise RuntimeError(f"获取定理详情失败: {e}")
    
    async def search_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        按分类搜索
        
        Args:
            category: 数学分类
            limit: 返回结果数量限制
        
        Returns:
            搜索结果列表
        """
        if not self.session:
            raise RuntimeError("MCP 客户端未连接，请先调用 connect()")
        
        try:
            result = await self.session.call_tool(
                "search_category",
                arguments={
                    "category": category,
                    "limit": limit
                }
            )
            
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return json.loads(content.text)
                elif hasattr(content, 'data'):
                    return content.data
            
            return []
            
        except Exception as e:
            logger.error(f"分类搜索失败: {e}")
            raise RuntimeError(f"分类搜索失败: {e}")
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        获取可用的工具列表
        
        Returns:
            可用工具列表
        """
        if not self.session:
            raise RuntimeError("MCP 客户端未连接，请先调用 connect()")
        
        try:
            result = await self.session.list_tools()
            return [tool.model_dump() for tool in result.tools]
        except Exception as e:
            logger.error(f"获取工具列表失败: {e}")
            raise RuntimeError(f"获取工具列表失败: {e}")
    
    async def get_server_info(self) -> Dict[str, Any]:
        """
        获取服务器信息
        
        Returns:
            服务器信息
        """
        if not self.session:
            raise RuntimeError("MCP 客户端未连接，请先调用 connect()")
        
        try:
            result = await self.session.get_server_info()
            return {
                "name": result.name,
                "version": result.version,
                "capabilities": result.capabilities.model_dump() if result.capabilities else {}
            }
        except Exception as e:
            logger.error(f"获取服务器信息失败: {e}")
            raise RuntimeError(f"获取服务器信息失败: {e}")


class SyncMCPLeanExploreClient:
    """
    MCP LeanExplore 客户端的同步包装器
    提供同步接口以便在非异步环境中使用
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.async_client = MCPLeanExploreClient(config_path)
        self.loop = None
    
    def _run_async(self, coro):
        """运行异步协程"""
        if self.loop is None:
            try:
                # 尝试获取当前事件循环
                self.loop = asyncio.get_event_loop()
            except RuntimeError:
                # 如果没有事件循环，创建新的
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
        
        return self.loop.run_until_complete(coro)
    
    def connect(self):
        """连接到 MCP 服务器"""
        return self._run_async(self.async_client.connect())
    
    def disconnect(self):
        """断开 MCP 连接"""
        return self._run_async(self.async_client.disconnect())
    
    def search(self, query: str, limit: int = 10, search_type: str = 'all') -> List[Dict[str, Any]]:
        """搜索数学知识和定理"""
        return self._run_async(self.async_client.search(query, limit, search_type))
    
    def get_theorem_details(self, theorem_id: str) -> Dict[str, Any]:
        """获取定理详细信息"""
        return self._run_async(self.async_client.get_theorem_details(theorem_id))
    
    def search_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """按分类搜索"""
        return self._run_async(self.async_client.search_by_category(category, limit))
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用的工具列表"""
        return self._run_async(self.async_client.get_available_tools())
    
    def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        return self._run_async(self.async_client.get_server_info())
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()