# RAG 功能測試計劃

> 日期：2025-01-26
> 目的：測試口語化理解與複雜語意分解功能

---

## 📋 測試概覽

| 測試類別 | 測試數量 | 說明 |
|----------|----------|------|
| 基礎功能 | 5 題 | 確認基本 RAG 運作 |
| 口語化理解 | 10 題 | 日常對話風格查詢 |
| 複雜語意分解 | 10 題 | 多面向問題拆解 |
| 邊界測試 | 5 題 | 極端情況處理 |

---

## 🎯 測試前準備

### 1. 測試文件
建議上傳這些類型的 PDF：
- 技術論文（如 CLIP、Transformer、BERT）
- 中文文件
- 混合中英文文件

### 2. 環境確認
```powershell
# 確認後端運行
curl http://localhost:8000/health

# 確認有文件
curl http://localhost:8000/documents

# 確認 Qdrant 有數據
curl http://localhost:8000/debug/qdrant
```

---

## 🧪 測試一：基礎功能測試

### 目的
確認 RAG 基本運作正常

### 測試用例

| # | 輸入 | 預期行為 |
|---|------|----------|
| B1 | `什麼是 attention?` | 返回 attention 相關內容 |
| B2 | `CLIP 是什麼?` | 返回 CLIP 論文內容 |
| B3 | `列出文件中的關鍵概念` | 返回多個概念摘要 |
| B4 | `第3頁講了什麼?` | 返回特定頁面內容 |
| B5 | `搜尋 neural network` | 返回神經網路相關段落 |

### 評估標準
- ✅ 返回相關內容
- ✅ 引用來源（檔名、頁碼）
- ✅ 回應時間 < 10 秒

---

## 🗣️ 測試二：口語化理解測試

### 目的
測試系統能否理解日常對話風格的問題

### 測試用例

| # | 口語輸入 | 系統應理解為 | 預期查詢擴展 |
|---|----------|--------------|--------------|
| O1 | `這篇在講啥` | 論文主旨摘要 | main contribution, abstract, overview |
| O2 | `有沒有講到圖片的部分` | 圖像相關內容 | image, visual, picture, 圖像, 視覺 |
| O3 | `他們怎麼訓練的啊` | 訓練方法 | training, method, loss function, optimizer |
| O4 | `結果好不好` | 實驗結果 | results, performance, accuracy, benchmark |
| O5 | `跟其他方法比起來怎樣` | 比較分析 | comparison, baseline, previous work, SOTA |
| O6 | `這個能幹嘛` | 應用場景 | application, use case, downstream task |
| O7 | `有什麼限制嗎` | 限制與缺點 | limitation, weakness, future work |
| O8 | `數據集用哪些` | 數據集資訊 | dataset, training data, benchmark |
| O9 | `模型架構長怎樣` | 模型結構 | architecture, model, structure, layer |
| O10 | `這篇的創新點是什麼` | 創新貢獻 | novelty, contribution, innovation |

### 後端日誌預期
應該看到 Planner 將口語轉換為多個查詢：
```
🧠 [Planner] 用戶輸入: 這篇在講啥
🧠 [Planner] 生成查詢:
  - main contribution
  - abstract summary
  - paper overview
  - 論文主旨
```

### 評估標準
- ✅ 口語被正確理解
- ✅ 生成多個相關查詢
- ✅ 返回相關內容
- ✅ 中英文查詢都有

---

## 🧩 測試三：複雜語意分解測試

### 目的
測試系統能否將複雜問題拆解成多個子查詢

### 測試用例

| # | 複雜問題 | 預期分解 |
|---|----------|----------|
| C1 | `比較 CLIP 和傳統 CNN 在圖像分類上的差異` | 1. CLIP image classification<br>2. CNN image classification<br>3. CLIP vs CNN comparison |
| C2 | `解釋 attention 機制如何幫助模型理解長文本` | 1. attention mechanism<br>2. long text understanding<br>3. attention benefits |
| C3 | `這個模型的訓練成本和推理速度如何？` | 1. training cost<br>2. inference speed<br>3. computational requirements |
| C4 | `論文中提到的 zero-shot 和 few-shot 學習有什麼不同？` | 1. zero-shot learning<br>2. few-shot learning<br>3. zero-shot vs few-shot |
| C5 | `作者如何處理多語言和跨模態的問題？` | 1. multilingual processing<br>2. cross-modal learning<br>3. language-vision alignment |
| C6 | `從數據預處理到模型部署的完整流程是什麼？` | 1. data preprocessing<br>2. model training<br>3. model deployment |
| C7 | `這個方法在醫療影像和自動駕駛領域的潛在應用？` | 1. medical imaging application<br>2. autonomous driving application<br>3. domain adaptation |
| C8 | `對比 Transformer 和 RNN 在序列建模上的優缺點` | 1. Transformer sequence modeling<br>2. RNN sequence modeling<br>3. Transformer vs RNN |
| C9 | `模型如何平衡準確率和計算效率？` | 1. model accuracy<br>2. computational efficiency<br>3. accuracy-efficiency tradeoff |
| C10 | `從理論創新和工程實現兩個角度評價這篇論文` | 1. theoretical contribution<br>2. engineering implementation<br>3. paper evaluation |

### 後端日誌預期
應該看到複雜問題被分解：
```
🧠 [Planner] 用戶輸入: 比較 CLIP 和傳統 CNN 在圖像分類上的差異
🧠 [Planner] 識別到比較型問題，進行分解
🧠 [Planner] 生成任務:
  - Task 1: rag_search "CLIP image classification"
  - Task 2: rag_search "CNN image classification"  
  - Task 3: rag_search "CLIP CNN comparison difference"
```

### 評估標準
- ✅ 問題被正確分解
- ✅ 多個子查詢被執行
- ✅ 結果被綜合整理
- ✅ 回答覆蓋所有面向

---

## ⚠️ 測試四：邊界測試

### 目的
測試系統對極端情況的處理

### 測試用例

| # | 輸入 | 預期行為 |
|---|------|----------|
| E1 | `？？？` | 友善提示無法理解 |
| E2 | `告訴我關於量子力學的一切`（文件中沒有） | 誠實回答找不到相關資訊 |
| E3 | `這篇論文的作者的寵物叫什麼名字` | 回答無此資訊 |
| E4 | 空白輸入 | 提示請輸入問題 |
| E5 | 超長輸入（500字以上） | 正常處理或友善截斷 |

---

## 📊 測試執行腳本

### 自動化測試腳本

```python
# test_rag.py
import requests
import json
import time

BASE_URL = "http://localhost:8000"

# 測試用例
TEST_CASES = {
    "basic": [
        "什麼是 attention?",
        "CLIP 是什麼?",
    ],
    "colloquial": [
        "這篇在講啥",
        "有沒有講到圖片的部分",
        "他們怎麼訓練的啊",
        "結果好不好",
        "跟其他方法比起來怎樣",
    ],
    "complex": [
        "比較 CLIP 和傳統 CNN 在圖像分類上的差異",
        "解釋 attention 機制如何幫助模型理解長文本",
        "這個模型的訓練成本和推理速度如何？",
    ],
    "edge": [
        "？？？",
        "告訴我關於量子力學的一切",
    ]
}

def test_chat(message: str, category: str):
    """測試對話功能"""
    print(f"\n{'='*60}")
    print(f"📝 類別: {category}")
    print(f"📝 輸入: {message}")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/stream",
            json={
                "message": message,
                "session_id": "test_session"
            },
            stream=True,
            timeout=60
        )
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith("data: "):
                    data = line_text[6:]
                    if data != "[DONE]":
                        try:
                            event = json.loads(data)
                            if event.get("type") == "content":
                                full_response += event.get("content", "")
                        except:
                            pass
        
        elapsed = time.time() - start_time
        
        print(f"✅ 回應 ({elapsed:.2f}秒):")
        print(full_response[:500] + "..." if len(full_response) > 500 else full_response)
        
        return {
            "success": True,
            "response": full_response,
            "time": elapsed
        }
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def run_all_tests():
    """執行所有測試"""
    results = {}
    
    for category, cases in TEST_CASES.items():
        print(f"\n\n{'#'*60}")
        print(f"### 測試類別: {category.upper()}")
        print(f"{'#'*60}")
        
        results[category] = []
        for case in cases:
            result = test_chat(case, category)
            results[category].append({
                "input": case,
                **result
            })
            time.sleep(2)  # 避免 rate limit
    
    # 輸出摘要
    print("\n\n" + "="*60)
    print("📊 測試摘要")
    print("="*60)
    
    for category, tests in results.items():
        success_count = sum(1 for t in tests if t.get("success"))
        print(f"{category}: {success_count}/{len(tests)} 成功")
    
    return results

if __name__ == "__main__":
    run_all_tests()
```

### 執行測試

```powershell
# 儲存上面的腳本為 test_rag.py
py test_rag.py
```

---

## 📈 評估指標

### 量化指標

| 指標 | 計算方式 | 目標值 |
|------|----------|--------|
| 回應率 | 成功回應數 / 總測試數 | > 95% |
| 平均回應時間 | 總時間 / 測試數 | < 10 秒 |
| 相關性 | 人工評分 1-5 分 | > 3.5 |
| 分解準確率 | 正確分解數 / 複雜問題數 | > 80% |

### 質化評估

| 項目 | 評估方式 |
|------|----------|
| 口語理解 | 是否正確理解非正式表達 |
| 查詢擴展 | 是否生成多角度查詢 |
| 答案完整性 | 是否涵蓋問題所有面向 |
| 引用準確性 | 來源引用是否正確 |

---

## 📝 測試記錄表

### 口語化測試記錄

| # | 輸入 | 理解正確 | 查詢擴展 | 結果相關 | 備註 |
|---|------|----------|----------|----------|------|
| O1 | 這篇在講啥 | □ | □ | □ | |
| O2 | 有沒有講到圖片的部分 | □ | □ | □ | |
| O3 | 他們怎麼訓練的啊 | □ | □ | □ | |
| O4 | 結果好不好 | □ | □ | □ | |
| O5 | 跟其他方法比起來怎樣 | □ | □ | □ | |

### 複雜語意分解記錄

| # | 輸入 | 分解正確 | 子查詢數 | 綜合答案 | 備註 |
|---|------|----------|----------|----------|------|
| C1 | 比較 CLIP 和 CNN... | □ | | □ | |
| C2 | attention 如何幫助... | □ | | □ | |
| C3 | 訓練成本和推理速度... | □ | | □ | |

---

## 🔍 如何觀察 Planner 行為

### 後端日誌關鍵字

```
# 開啟 DEBUG 模式查看更多細節
# 在 .env 中設定：LOG_LEVEL=DEBUG
```

### 觀察重點

1. **口語轉換**
```
🧠 [Planner] 偵測到口語化表達
🧠 [Planner] 原始: "這篇在講啥"
🧠 [Planner] 轉換: ["main contribution", "abstract", "overview"]
```

2. **問題分解**
```
🧠 [Planner] 偵測到複雜問題（比較型）
🧠 [Planner] 分解為 3 個子任務
```

3. **多查詢執行**
```
🔍 [Executor] 執行任務 1/3: rag_search
🔍 [Executor] 執行任務 2/3: rag_search
🔍 [Executor] 執行任務 3/3: rag_search
✅ [Executor] 合併 3 個結果
```

---

## 🚀 開始測試

### 快速測試（手動）

1. 開啟前端 http://localhost:5173
2. 依序輸入測試問題
3. 觀察後端日誌
4. 記錄結果

### 完整測試（自動）

```powershell
# 執行自動化測試腳本
py test_rag.py > test_results.txt
```

---

準備好了嗎？請先確認：
1. ✅ 後端正在運行
2. ✅ 已上傳至少一個 PDF
3. ✅ `/debug/qdrant` 顯示有數據

然後開始測試！
