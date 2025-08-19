#!/usr/bin/env python3

from proof_assistant import ProofProcessor

def test_addition_zero():
    """
    测试证明：对所有自然数 n，有 n + 0 = n
    """
    proof_statement = "证明对所有自然数 n，有 n + 0 = n。（加法的零元素性质）"
    
    try:
        processor = ProofProcessor(config_path="config/config.yaml")
        result = processor.process_proof(proof_statement)
        
        print("\n=== 证明结果 ===")
        print(result)
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == '__main__':
    test_addition_zero()