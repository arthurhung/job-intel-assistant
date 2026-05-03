# Job Intel Assistant Roadmap

這個 side project 的定位是：自動蒐集職缺、清洗資料、分析技能需求，並根據履歷匹配度提醒值得投遞的工作。

## Phase 1 - CLI MVP

目標：先做出一條能跑通的本地資料流程，證明核心概念。

狀態：已完成基礎版。

- 從 CSV 匯入職缺資料
- 使用 SQLite 儲存職缺
- 從 PDF/TXT 讀取履歷文字
- 用技能關鍵字計算履歷與職缺匹配分數
- 產生 Markdown match report
- 依分數排序職缺

## Phase 2 - Telegram Notification

目標：在產生匹配結果後，把高分職缺主動推送給使用者。

狀態：已完成 CLI 整合。

- 使用 Telegram Bot API 發送通知
- 支援 `TELEGRAM_BOT_TOKEN` 與 `TELEGRAM_CHAT_ID` 環境變數
- 支援最低通知分數門檻
- 支援限制推送職缺數量
- 保留 Markdown report 作為完整結果

後續可擴充：

- 加入「沒有高分職缺就不通知」模式
- 加入 daily digest 格式
- 支援多個通知 channel，例如 Email、Line、Discord

## Phase 3 - Crawler Adapters

目標：從手動 CSV 匯入，升級成自動蒐集職缺。

狀態：已完成 adapter 架構與 sample crawler。

- 建立 `crawler` interface
- 支援 CLI：`python -m job_intel crawl --source sample`
- 支援 API：`POST /api/crawl`
- Dashboard 可手動觸發 sample crawler
- 正規化欄位：source、external_id、title、company、location、url、description、salary、posted_at
- 用 `source + external_id` 做去重
- 保留 raw description，方便之後做 LLM enrichment

後續可擴充：

- 先支援 1 個真實職缺來源，例如 Cake、Yourator，或公司 career page
- 加入 crawler error handling 與 rate limit
- 儲存 crawl run history，記錄每次匯入數量與錯誤

## Phase 4 - LLM Job Analysis

目標：讓工具不只做關鍵字比對，而是能產生更像求職助理的分析。

- 擷取職缺技能要求
- 判斷職缺等級：junior / mid / senior
- 摘要工作內容與加分條件
- 產生履歷修改建議
- 產生可能面試重點
- 將 LLM 輸出存成結構化 JSON

## Phase 5 - Airflow Pipeline

目標：把職缺蒐集、清洗、分析、通知變成可觀測、可重跑的資料管線。

建議 DAG：

```text
crawl_jobs
-> normalize_jobs
-> deduplicate_jobs
-> analyze_with_llm
-> match_resume
-> send_telegram_notification
```

展示重點：

- 排程資料管線
- task retry 與失敗觀測
- backfill 歷史職缺資料
- 將 Telegram 通知作為 pipeline 最後一段

## Phase 6 - Web Dashboard

目標：提供一個可以展示作品集的操作介面。

狀態：已完成基礎版。

- 查看職缺列表
- 依技能、公司、地點、匹配分數篩選
- 顯示履歷匹配原因
- 提供手動觸發 match / notification 的按鈕

注意：Telegram token 不應放在前端，前端只呼叫後端 API，由後端負責發送通知。

後續可擴充：

- 標記狀態：想投、已投、面試中、拒絕
- 上傳履歷檔案，而不是只貼文字
- 顯示歷史匹配紀錄
- 加入 FastAPI auth，支援單使用者部署

## Phase 7 - Docker and Kubernetes

目標：展示 production-minded deployment 能力。

Docker Compose：

- FastAPI backend
- PostgreSQL
- Airflow
- Redis 或 Airflow executor 需要的 queue

Kubernetes：

- Backend Deployment / Service
- Airflow scheduler / webserver / worker
- PostgreSQL 可先用外部服務或 dev-only manifest
- Secret 管理 Telegram token、LLM API key、DB password
- ConfigMap 管理排程與 app 設定
- Ingress 對外暴露 dashboard
- CronJob 可作為簡化版排程替代方案

## Portfolio Narrative

這個專案可以包裝成：

> Built a data-driven job intelligence assistant with scheduled ETL pipelines, resume-job matching, Telegram notifications, LLM-based job analysis, and containerized deployment.

第一版重點是跑通核心流程；第二階段開始加入自動化、LLM、Airflow 與 Kubernetes，讓它從小工具升級成完整的 backend/data engineering/LLM app 作品。
