#!/usr/bin/env python3

from proof_assistant import ProofProcessor

def test_single_proof():
    """
    测试单个证明
    """
    # 先测试最简单的证明
    proof_statement = "证明对所有自然数 n，有 n + 0 = n。（加法的零元素性质）"
    
    try:
        processor = ProofProcessor(config_path="config/config.yaml")
        result = processor.process_proof(proof_statement)
        
        print("=== 证明结果 ===")
        print(result)
        print("\n✅ 测试完成！")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_single_proof()