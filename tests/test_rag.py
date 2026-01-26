"""
RAG 功能測試腳本
測試口語化理解與複雜語意分解

使用方式：
    py test_rag.py              # 執行所有測試
    py test_rag.py --basic      # 只測試基礎功能
    py test_rag.py --colloquial # 只測試口語化
    py test_rag.py --complex    # 只測試複雜分解
"""

import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

# ============================================
# 測試用例定義
# ============================================

TEST_CASES = {
    "basic": {
        "name": "基礎功能測試",
        "description": "確認 RAG 基本運作",
        "cases": [
            {"input": "什麼是 attention?", "expect": "attention 相關內容"},
            {"input": "這篇論文的主題是什麼?", "expect": "論文主題摘要"},
            {"input": "搜尋 neural network", "expect": "神經網路相關段落"},
        ]
    },
    
    "colloquial": {
        "name": "口語化理解測試",
        "description": "測試系統理解日常口語的能力",
        "cases": [
            {"input": "這篇在講啥", "expect": "論文主旨摘要", "should_expand": True},
            {"input": "有沒有講到圖片的部分", "expect": "圖像相關內容", "should_expand": True},
            {"input": "他們怎麼訓練的啊", "expect": "訓練方法", "should_expand": True},
            {"input": "結果好不好", "expect": "實驗結果", "should_expand": True},
            {"input": "跟其他方法比起來怎樣", "expect": "比較分析", "should_expand": True},
            {"input": "這個能幹嘛", "expect": "應用場景", "should_expand": True},
            {"input": "有什麼限制嗎", "expect": "限制與缺點", "should_expand": True},
            {"input": "數據集用哪些", "expect": "數據集資訊", "should_expand": True},
            {"input": "模型架構長怎樣", "expect": "模型結構", "should_expand": True},
            {"input": "這篇的亮點是什麼", "expect": "創新貢獻", "should_expand": True},
        ]
    },
    
    "complex": {
        "name": "複雜語意分解測試",
        "description": "測試系統將複雜問題拆解的能力",
        "cases": [
            {
                "input": "比較這個方法和傳統方法的差異",
                "expect": "比較分析",
                "should_decompose": True,
                "expected_subtasks": ["新方法特點", "傳統方法", "比較差異"]
            },
            {
                "input": "這個模型的訓練成本和推理速度如何？",
                "expect": "成本與速度分析",
                "should_decompose": True,
                "expected_subtasks": ["訓練成本", "推理速度"]
            },
            {
                "input": "從數據預處理到模型部署的完整流程是什麼？",
                "expect": "完整流程說明",
                "should_decompose": True,
                "expected_subtasks": ["數據預處理", "模型訓練", "模型部署"]
            },
            {
                "input": "模型如何平衡準確率和計算效率？",
                "expect": "權衡分析",
                "should_decompose": True,
                "expected_subtasks": ["準確率", "計算效率", "權衡方法"]
            },
            {
                "input": "論文中的理論貢獻和實際應用分別是什麼？",
                "expect": "雙面向分析",
                "should_decompose": True,
                "expected_subtasks": ["理論貢獻", "實際應用"]
            },
        ]
    },
    
    "edge": {
        "name": "邊界測試",
        "description": "測試極端情況處理",
        "cases": [
            {"input": "？？？", "expect": "友善提示"},
            {"input": "告訴我關於量子力學的一切", "expect": "找不到相關資訊"},
            {"input": "", "expect": "提示輸入問題"},
        ]
    }
}


# ============================================
# 測試函數
# ============================================

def check_backend():
    """檢查後端是否運行"""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        return r.status_code == 200
    except:
        return False


def check_documents():
    """檢查是否有文件"""
    try:
        r = requests.get(f"{BASE_URL}/documents", timeout=5)
        data = r.json()
        docs = data.get("documents", [])
        return len(docs) > 0, docs
    except Exception as e:
        return False, str(e)


def test_search(query: str):
    """測試搜尋功能"""
    try:
        r = requests.post(
            f"{BASE_URL}/search",
            json={"query": query, "top_k": 3},
            timeout=30
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def test_chat(message: str, selected_docs: list = None):
    """測試對話功能（串流）"""
    start_time = time.time()
    
    try:
        payload = {
            "message": message,
            "session_id": f"test_{int(time.time())}"
        }
        if selected_docs:
            payload["selected_docs"] = selected_docs
        
        response = requests.post(
            f"{BASE_URL}/chat/stream",
            json=payload,
            stream=True,
            timeout=60
        )
        
        full_response = ""
        sources = []
        thinking = ""
        tool_calls = []
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith("data: "):
                    data = line_text[6:]
                    if data == "[DONE]":
                        break
                    try:
                        event = json.loads(data)
                        event_type = event.get("type", "")
                        
                        if event_type == "content":
                            full_response += event.get("content", "")
                        elif event_type == "thinking":
                            thinking += event.get("content", "")
                        elif event_type == "tool_call":
                            tool_calls.append(event)
                        elif event_type == "sources":
                            sources = event.get("sources", [])
                    except:
                        pass
        
        elapsed = time.time() - start_time
        
        return {
            "success": True,
            "response": full_response,
            "sources": sources,
            "thinking": thinking,
            "tool_calls": tool_calls,
            "time": elapsed
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "time": time.time() - start_time
        }


def run_category_tests(category: str, cases_data: dict):
    """執行某類別的所有測試"""
    print(f"\n{'='*70}")
    print(f"📂 {cases_data['name']}")
    print(f"   {cases_data['description']}")
    print(f"{'='*70}")
    
    results = []
    
    for i, case in enumerate(cases_data['cases'], 1):
        input_text = case['input']
        expected = case.get('expect', '')
        
        print(f"\n[{i}/{len(cases_data['cases'])}] 測試: {input_text[:50]}...")
        print("-" * 50)
        
        # 執行測試
        result = test_chat(input_text)
        
        if result['success']:
            response_preview = result['response'][:200] + "..." if len(result['response']) > 200 else result['response']
            print(f"✅ 成功 ({result['time']:.2f}秒)")
            print(f"📝 回應: {response_preview}")
            
            if result['sources']:
                print(f"📚 來源: {len(result['sources'])} 個")
            
            if result['tool_calls']:
                print(f"🔧 工具呼叫: {len(result['tool_calls'])} 次")
        else:
            print(f"❌ 失敗: {result.get('error', 'Unknown error')}")
        
        results.append({
            "input": input_text,
            "expected": expected,
            **result
        })
        
        # 避免 rate limit
        time.sleep(1)
    
    return results


def print_summary(all_results: dict):
    """輸出測試摘要"""
    print("\n\n" + "=" * 70)
    print("📊 測試摘要")
    print("=" * 70)
    
    total_tests = 0
    total_success = 0
    total_time = 0
    
    for category, results in all_results.items():
        success = sum(1 for r in results if r.get('success'))
        total = len(results)
        avg_time = sum(r.get('time', 0) for r in results) / total if total > 0 else 0
        
        total_tests += total
        total_success += success
        total_time += sum(r.get('time', 0) for r in results)
        
        status = "✅" if success == total else "⚠️" if success > 0 else "❌"
        print(f"{status} {category}: {success}/{total} 成功, 平均 {avg_time:.2f}秒")
    
    print("-" * 70)
    overall_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
    avg_overall_time = total_time / total_tests if total_tests > 0 else 0
    print(f"總計: {total_success}/{total_tests} ({overall_rate:.1f}%), 平均回應時間: {avg_overall_time:.2f}秒")


def save_results(all_results: dict):
    """儲存測試結果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 結果已儲存至: {filename}")


# ============================================
# 主程式
# ============================================

def main():
    print("=" * 70)
    print("🧪 OpenCode Platform - RAG 功能測試")
    print(f"   時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 檢查後端
    print("\n🔍 檢查環境...")
    
    if not check_backend():
        print("❌ 後端未運行！請先啟動: py -m cli.main api")
        return
    print("✅ 後端正常")
    
    has_docs, docs = check_documents()
    if not has_docs:
        print("❌ 沒有文件！請先上傳 PDF")
        return
    print(f"✅ 找到 {len(docs)} 個文件: {[d.get('name', d) for d in docs[:3]]}...")
    
    # 決定要測試哪些類別
    categories_to_test = []
    
    if len(sys.argv) > 1:
        arg = sys.argv[1].replace("--", "")
        if arg in TEST_CASES:
            categories_to_test = [arg]
        else:
            print(f"未知參數: {arg}")
            print("可用參數: --basic, --colloquial, --complex, --edge")
            return
    else:
        categories_to_test = list(TEST_CASES.keys())
    
    # 執行測試
    all_results = {}
    
    for category in categories_to_test:
        results = run_category_tests(category, TEST_CASES[category])
        all_results[category] = results
    
    # 輸出摘要
    print_summary(all_results)
    
    # 儲存結果
    save_results(all_results)
    
    print("\n🎉 測試完成！")


if __name__ == "__main__":
    main()
