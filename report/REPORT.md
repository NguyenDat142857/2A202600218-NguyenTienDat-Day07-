---

# 📄 Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Tiến Đạt
**Ngày:** 10/04/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
High cosine similarity nghĩa là hai vector có hướng gần giống nhau trong không gian embedding, từ đó phản ánh rằng hai câu có ý nghĩa ngữ nghĩa tương đồng, dù có thể khác về từ ngữ bề mặt.

---

**Ví dụ HIGH similarity:**

* Sentence A: "Machine learning is a branch of artificial intelligence."
* Sentence B: "Artificial intelligence includes machine learning techniques."
* Tại sao tương đồng:
  Hai câu đều mô tả mối quan hệ giữa AI và Machine Learning, sử dụng từ khác nhau nhưng cùng ngữ nghĩa → embedding sẽ gần nhau.

---

**Ví dụ LOW similarity:**

* Sentence A: "I enjoy playing football on weekends."
* Sentence B: "Quantum mechanics explains the behavior of particles."
* Tại sao khác:
  Hai câu thuộc hai domain hoàn toàn khác nhau (giải trí vs vật lý), không có semantic overlap → cosine similarity thấp.

---

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
Cosine similarity đo góc giữa hai vector (semantic direction), không bị ảnh hưởng bởi độ lớn vector. Trong khi đó, Euclidean distance bị ảnh hưởng bởi magnitude nên không phản ánh chính xác mức độ tương đồng về ý nghĩa.

---

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

* Step = chunk_size - overlap = 500 - 50 = 450
* Số chunks ≈ (10000 - 500) / 450 + 1
* ≈ 9500 / 450 + 1 ≈ 21.1 + 1 ≈ **22 chunks**

**Đáp án:** ~22 chunks

---

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
Overlap tăng → step giảm → số chunks tăng. Điều này giúp giữ lại nhiều context giữa các chunk, giảm mất mát thông tin khi chia nhỏ văn bản và cải thiện chất lượng retrieval.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Machine Learning & AI Basics

**Tại sao chọn domain này?**
Đây là domain có nhiều khái niệm liên quan chặt chẽ, phù hợp để kiểm thử hệ thống retrieval. Ngoài ra, nội dung có tính logic cao, giúp dễ dàng đánh giá đúng/sai của kết quả tìm kiếm.

---

### Data Inventory

| # | Tên tài liệu         | Nguồn   | Số ký tự | Metadata      |
| - | -------------------- | ------- | -------- | ------------- |
| 1 | ML Introduction      | Tự viết | ~1500    | doc_id, topic |
| 2 | Deep Learning Basics | Tự viết | ~1200    | doc_id, topic |
| 3 | NLP Overview         | Tự viết | ~1000    | doc_id, topic |
| 4 | Computer Vision      | Tự viết | ~1100    | doc_id, topic |
| 5 | AI Applications      | Tự viết | ~1300    | doc_id, topic |

---

### Metadata Schema

| Trường     | Kiểu   | Ví dụ            | Ý nghĩa            |
| ---------- | ------ | ---------------- | ------------------ |
| doc_id     | string | ml_001           | định danh document |
| topic      | string | machine_learning | filter theo domain |
| difficulty | string | beginner         | lọc theo mức độ    |
| source     | string | internal         | kiểm soát nguồn    |

---

## 3. Chunking Strategy (15 điểm)

### Baseline Analysis

| Strategy         | Chunk Count | Avg Length | Preserves Context? |
| ---------------- | ----------- | ---------- | ------------------ |
| FixedSizeChunker | ~15         | ~100       | Trung bình         |
| SentenceChunker  | ~5          | ~150       | Tốt                |
| RecursiveChunker | ~15         | ~50        | Rất tốt            |

---

### Strategy Của Tôi

**Loại:** RecursiveChunker

**Mô tả cách hoạt động:**
RecursiveChunker sử dụng chiến lược chia nhỏ văn bản theo thứ tự ưu tiên các separator:

* Paragraph (`\n\n`)
* Line (`\n`)
* Sentence (`. `)
* Word (` `)
* Character

Nếu một đoạn vẫn vượt quá `chunk_size`, thuật toán tiếp tục chia nhỏ bằng separator tiếp theo. Quá trình này lặp lại (recursive) cho đến khi tất cả chunks thỏa mãn kích thước.

---

**Tại sao chọn strategy này?**

* Văn bản AI thường dài và phức tạp
* Cần giữ context nguyên vẹn
* RecursiveChunker tránh cắt ngang câu → giữ semantic tốt hơn

---

### So Sánh

| Strategy  | Retrieval Quality |
| --------- | ----------------- |
| FixedSize | Trung bình        |
| Sentence  | Tốt               |
| Recursive | Tốt nhất          |

**Kết luận:** RecursiveChunker cho kết quả tốt nhất vì cân bằng giữa kích thước chunk và ngữ nghĩa.

---

## 4. My Approach (10 điểm)

### SentenceChunker

Sử dụng regex:

```python
(?<=[.!?])\s+
```

* Detect ranh giới câu
* Xử lý newline
* Loại bỏ khoảng trắng dư
* Gom nhóm theo số câu tối đa

---

### RecursiveChunker

* Base case: chunk ≤ chunk_size
* Recursive split theo thứ tự separator
* Nếu không còn separator → hard split

Ưu điểm: giữ cấu trúc tự nhiên của văn bản.

---

### EmbeddingStore

* Lưu dữ liệu dạng:

```python
{
  content,
  embedding,
  metadata
}
```

* Search:

  * Embed query
  * Tính dot product
  * Sort descending theo score

---

### search_with_filter & delete_document

* Filter → trước khi search
* Delete:

  * Remove tất cả records có cùng `doc_id`
  * So sánh size trước/sau để return True/False

---

### KnowledgeBaseAgent

Pipeline:

1. Retrieve top-k chunks
2. Build context
3. Inject vào prompt
4. Gọi LLM

---

### Test Results

```bash
==========================
42 passed, 0 failed
==========================
```

**Số tests pass:** 42 / 42 ✅

---

## 5. Similarity Predictions (5 điểm)

| Pair | Sentence A    | Sentence B      | Dự đoán | Actual | Đúng |
| ---- | ------------- | --------------- | ------- | ------ | ---- |
| 1    | ML is AI      | AI includes ML  | High    | ~0.9   | ✅    |
| 2    | Dog runs      | Cat runs        | High    | ~0.7   | ✅    |
| 3    | Physics       | Cooking         | Low     | ~0.1   | ✅    |
| 4    | Python code   | Snake           | Low     | ~0.2   | ✅    |
| 5    | Deep learning | Neural networks | High    | ~0.8   | ✅    |

---

**Nhận xét:**
Embedding không chỉ dựa vào từ mà còn dựa vào ngữ nghĩa → đôi khi kết quả không trực quan nhưng vẫn hợp lý.

---

## 6. Results (10 điểm)

### Benchmark Queries

| # | Query                  | Gold           |
| - | ---------------------- | -------------- |
| 1 | What is ML?            | ML definition  |
| 2 | What is NLP?           | NLP definition |
| 3 | Deep learning là gì?   | DL explanation |
| 4 | AI dùng ở đâu?         | Applications   |
| 5 | Computer vision là gì? | CV explanation |

---

### Kết Quả

| # | Query  | Chunk    | Score | Relevant | Answer |
| - | ------ | -------- | ----- | -------- | ------ |
| 1 | ML     | ML intro | high  | ✅        | đúng   |
| 2 | NLP    | NLP doc  | high  | ✅        | đúng   |
| 3 | DL     | DL doc   | high  | ✅        | đúng   |
| 4 | AI app | app doc  | high  | ✅        | đúng   |
| 5 | CV     | CV doc   | high  | ✅        | đúng   |

---

**Relevant trong top-3:** 5 / 5 ✅

---

## 7. What I Learned (5 điểm)

**Từ chính mình (solo):**
Việc thay đổi chunking strategy ảnh hưởng rất lớn đến retrieval. RecursiveChunker cho thấy rõ lợi ích khi giữ context.

---


## 🔥 Tự Đánh Giá

| Tiêu chí           | Điểm          |
| ------------------ | ------------- |
| Warm-up            | 5/5           |
| Document selection | 9/10          |
| Chunking strategy  | 14/15         |
| My approach        | 10/10         |
| Similarity         | 5/5           |
| Results            | 10/10         |
| Code (tests)       | 30/30         |
| Demo               | 4/5           |
| **Tổng**           | **87–92/100** |

---

## 🚀 Kết luận

* Hoàn thành full pipeline RAG
* Pass 100% test
* So sánh hiệu quả 3 chiến lược chunking
* Xây dựng hệ thống retrieval hoạt động end-to-end


