#!/usr/bin/env python3

from proof_assistant import ProofProcessor

def test_multiple_proofs():
    """
    测试多个不同类型的数学证明
    """
    proofs = [
        "证明对所有自然数 n，有 n + 0 = n。（加法的零元素性质）",
        "证明 ¬¬P → P 在经典逻辑下成立。（双重否定律）",
        "证明对任意自然数 n，若 n^2 是偶数，则 n 是偶数。（整数奇偶性）",
        "使用数学归纳法证明对所有自然数 n，有 n + n = 2n。（加法与乘法关系）",
        "证明若 A ⊆ B 且 B ⊆ C，则 A ⊆ C。（集合包含关系的传递性）"
    ]
    
    try:
        processor = ProofProcessor(config_path="config/config.yaml")
        
        for i, proof_statement in enumerate(proofs, 1):
            print(f"\n{'='*80}")
            print(f"证明 {i}/5")
            print('='*80)
            
            result = processor.process_proof(proof_statement)
            print(result)
            
            print(f"\n{'='*80}")
            print(f"证明 {i} 完成")
            print('='*80)
            
        print(f"\n🎉 所有 {len(proofs)} 个证明测试完成！")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_multiple_proofs()