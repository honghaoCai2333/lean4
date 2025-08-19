#!/usr/bin/env python3

import click
import sys
from pathlib import Path
from proof_assistant import ProofProcessor

@click.command()
@click.option('--proof', '-p', help='数学证明内容', required=True)
@click.option('--model', '-m', default='gpt-3.5-turbo', help='使用的AI模型')
@click.option('--config', '-c', default='config/config.yaml', help='配置文件路径')
def main(proof, model, config):
    """
    Lean4证明助手 - 使用LiteLLM和Lean4进行数学证明
    """
    try:
        processor = ProofProcessor(config_path=config, model=model)
        result = processor.process_proof(proof)
        
        print("\n=== 证明结果 ===")
        print(result)
        
    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    main()