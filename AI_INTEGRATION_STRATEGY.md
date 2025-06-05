# AI集成策略：交易异常检测

## 1. 引言 (Introduction)

### 1.1. 目的
本文档旨在详细规划“交易异常检测”AI功能模块如何设计、开发并融入审计项目管理系统（以下简称“核心系统”）。其目标是为核心系统开发团队和AI服务开发团队提供清晰的集成蓝图和技术指引，确保AI功能能够无缝、高效地与核心业务流程相结合。

### 1.2. AI功能概述
“交易异常检测”AI功能旨在利用机器学习算法（如 `transaction_anomaly_detection_prototype.ipynb` 中原型验证的孤立森林算法）自动分析大规模交易数据，识别潜在的异常模式、欺诈行为或控制缺陷。其核心价值在于：
*   **提升审计效率**：自动化初步筛选过程，使审计师能更专注于高风险领域。
*   **增强风险识别能力**：发现人工审计难以察觉的复杂或隐藏的异常模式。
*   **扩大审计覆盖面**：能够以较低成本分析全量或大样本量的交易数据。
原型验证已证明了该方法在模拟数据上的可行性，并指出了在真实场景中需要关注的特征工程、模型选择和评估等方面的挑战。

## 2. 数据流与数据准备 (Data Flow and Preparation)

### 2.1. 交易数据来源假设 (Assumption of TransactionData Source)
*   **核心系统非数据存储主体**：明确核心审计系统本身不直接存储海量的原始交易流水数据。这样做是为了避免核心系统变得过于臃肿，并保持其专注于审计管理的核心业务流程。
*   **外部数据源导入/连接**：假设交易数据将主要通过以下方式提供给AI服务：
    *   **批量导入**：审计团队从被审计单位的系统（如ERP、财务系统、业务数据库）导出交易数据文件（如CSV, Excel, Parquet），然后上传至一个预定的存储位置（如对象存储）。
    *   **数据库连接**：在更高级的集成场景中，可能允许配置到外部数据仓库或特定交易数据库的只读连接，AI服务按需提取数据。
*   **接口与灵活性**：系统设计必须保留接入和处理不同来源、不同格式真实数据的接口和灵活性。AI服务需要具备处理多种数据输入方式的能力。

### 2.2. 数据接入点 (Data Ingestion Point)
为了在核心系统中管理和追踪用于AI分析的交易数据，提议引入一个新的概念模型：`TransactionDataset`（交易数据集）。此模型将与核心系统中的 `AuditProject`（审计项目）关联。
`TransactionDataset` 将存储以下元数据：
*   `id` (UUID): 唯一标识符。
*   `audit_project_id` (ForeignKey to AuditProject): 关联的审计项目。
*   `name` (CharField): 数据集的用户自定义名称（例如：“2023年度销售流水”，“Q4供应商付款数据”）。
*   `source_description` (TextField): 数据来源的文字描述（例如：“SAP系统导出”，“Oracle财务数据库直连”）。
*   `data_time_range_start` (DateField/DateTimeField): 数据集包含的交易的起始时间。
*   `data_time_range_end` (DateField/DateTimeField): 数据集包含的交易的结束时间。
*   `record_count` (IntegerField, nullable): 数据集中的大致记录（交易）数量。
*   `data_location_uri` (CharField/URLField): 数据的实际存储位置。
    *   对于文件：指向对象存储（如S3, MinIO, Azure Blob）中的文件路径。
    *   对于数据库连接：存储加密的连接字符串或指向一个安全的连接配置。
*   `data_schema_info` (JSONField, nullable): 描述数据结构（字段名、类型等）的元数据，有助于AI服务解析。
*   `status` (CharField): 数据集状态，例如 'New'（新创建/已上传元数据）, 'Uploading'（文件上传中）, 'Uploaded'（文件上传完成/可供处理）, 'Processing'（AI服务正在处理）, 'Analyzed'（分析完成）, 'Error'（处理失败）。
*   `uploaded_by` (ForeignKey to User): 上传或关联此数据集的用户。
*   `created_at` (DateTimeField): 元数据记录创建时间。
*   `updated_at` (DateTimeField): 元数据记录更新时间。

### 2.3. 数据预处理考虑 (Data Preprocessing Considerations - High Level)
数据预处理是AI模型成功的关键步骤。这些步骤可能在AI服务内部，或者在一个独立的数据准备服务/流程中执行：
*   **数据清洗**：处理缺失值、重复数据、格式错误等。
*   **格式转换**：将不同来源的数据（如CSV, Excel, JSON）转换为AI服务易于处理的内部格式（如Pandas DataFrame, Parquet）。
*   **特征选择与工程**：基于`transaction_anomaly_detection_prototype.ipynb`的经验，需要选择最相关的特征（如金额、数量、价格、时间戳特征），并可能创建新的交互特征或派生特征（如与历史平均值的偏差、交易频率等）。
*   **数据规范化/标准化**：根据所选模型的要求，可能需要对数值特征进行缩放。
*   **处理类别特征**：如`SecurityID`, `ClientID`等，可能需要进行编码（如One-Hot Encoding, Label Encoding, or Embeddings）。

## 3. AI服务集成架构 (AI Service Integration Architecture)

### 3.1. AI服务定位 (AI Service Positioning)
*   **独立服务部署**：遵循在 `ARCHITECTURE.md` 中定义的微服务/面向服务的架构原则，交易异常检测AI功能将作为一个独立的、可单独部署和扩展的服务（以下简称“AI检测服务”）。
*   **API交互**：核心审计系统通过定义良好的RESTful API与AI检测服务进行通信。这种松耦合的方式有利于独立开发、技术栈选择和维护。

### 3.2. 触发机制 (Triggering Mechanism)
*   **用户手动触发**：
    *   审计师在核心系统的某个审计项目（`AuditProject`）中，选择一个已准备好的 `TransactionDataset`。
    *   通过用户界面操作（如点击“开始异常检测”按钮）发起检测请求。
*   **(未来考虑) 自动/计划任务触发**：
    *   例如，当一个新的 `TransactionDataset` 状态变为 'Uploaded' 时，可配置为自动触发检测。
    *   或允许用户设定计划任务，在指定时间对特定类型的数据集进行定期检测。

### 3.3. 概念API设计 - 交易异常检测服务 (Conceptual API Design - Anomaly Detection Service)
以下是AI检测服务可能暴露的API端点（具体实现细节，如认证授权，将遵循整体架构设计）：

#### 3.3.1. 发起检测请求 (Initiate Detection Request)
*   **Endpoint:** `POST /api/ai/transaction-anomaly/detect`
*   **描述:** 核心系统调用此接口来启动一个新的交易异常检测任务。
*   **请求体 (Request Body - JSON):**
    ```json
    {
      "audit_project_id": "uuid",
      "transaction_dataset_id": "uuid",
      "data_location_uri": "s3://bucket-name/path/to/data.csv", // 从TransactionDataset获取
      "data_schema_info": { ... }, // (可选) 从TransactionDataset获取，或AI服务自行获取
      "sensitivity_level": "medium", // (可选) 检测敏感度: "low", "medium", "high"
      "anomaly_detection_parameters": { // (可选) 更细致的模型参数
          "algorithm": "IsolationForest", // 或 "auto"
          "n_estimators": 100,
          "contamination": "auto"
          // ... 其他模型特定参数
      }
    }
    ```
    *   `audit_project_id` 和 `transaction_dataset_id` 用于追踪和关联，AI服务本身可能不直接操作核心系统数据库。
*   **响应体 (Response Body - 异步操作确认):**
    ```json
    {
      "ai_detection_run_id": "uuid", // AI服务内部生成的本次检测任务的唯一ID
      "status": "PENDING", // 或 "RECEIVED", "PROCESSING_STARTED"
      "message": "交易异常检测任务已接收并启动处理"
    }
    ```

#### 3.3.2. 查询检测状态与结果 (Query Detection Status & Results)
*   **Endpoint:** `GET /api/ai/transaction-anomaly/runs/{ai_detection_run_id}`
*   **描述:** 核心系统通过此接口轮询AI检测任务的当前状态和初步结果（如果已完成）。
*   **路径参数:**
    *   `ai_detection_run_id`: AI服务在发起检测时返回的ID。
*   **响应体 (Response Body - 若仍在处理中):**
    ```json
    {
      "ai_detection_run_id": "uuid",
      "status": "PROCESSING", // 或 "FEATURE_ENGINEERING", "MODEL_TRAINING", "INFERENCE"
      "progress_percentage": 30, // (可选) 估计的处理进度
      "message": "正在进行特征工程..." // (可选) 更详细的状态消息
    }
    ```
*   **响应体 (Response Body - 若已完成):**
    ```json
    {
      "ai_detection_run_id": "uuid",
      "status": "COMPLETED", // 或 "COMPLETED_WITH_ERRORS", "FAILED"
      "started_at": "iso_timestamp",
      "completed_at": "iso_timestamp",
      "summary": {
        "total_transactions_processed": 1000000,
        "anomalies_found_count": 150,
        "error_message": null // 如果 status 是 FAILED 或 COMPLETED_WITH_ERRORS
      },
      "results_reference_id": "uuid" // 用于获取详细异常列表的ID (可能是ai_detection_run_id本身或新ID)
      // "results_storage_location": "s3://results-bucket/run_id/anomalies.parquet" // (可选) 结果文件的直接存储位置
    }
    ```

#### 3.3.3. 获取详细异常列表 (Get Detailed Anomalies)
*   **Endpoint:** `GET /api/ai/transaction-anomaly/results/{results_reference_id}/anomalies?page=1&page_size=50&min_score=0.7`
*   **描述:** 获取指定检测任务识别出的详细异常交易列表，支持分页和筛选。
*   **路径参数:**
    *   `results_reference_id`: 从上一个API获取的ID。
*   **查询参数 (Query Parameters):**
    *   `page`, `page_size`: 用于分页。
    *   `min_score` (float, 可选): 按最低异常分数筛选。
    *   `sort_by` (string, 可选): 排序字段 (如 `anomaly_score`, `transaction_date`)。
    *   `order` ('asc', 'desc', 可选): 排序方向。
*   **响应体 (Response Body - JSON):**
    ```json
    {
      "pagination": {
        "count": 150, // 总异常数
        "page": 1,
        "page_size": 50,
        "total_pages": 3,
        "next_url": "/api/ai/transaction-anomaly/results/.../anomalies?page=2...", // (可选)
        "previous_url": null // (可选)
      },
      "data": [
        {
          "transaction_identifier_in_source": "TXN_12345_ABC", // 原始数据中的唯一标识符
          "anomaly_score": 0.85, // 模型给出的异常分数
          "reason_codes": ["HIGH_AMOUNT", "UNUSUAL_TIME"], // (可选) AI模型提供的简要原因代码
          "explanation": "Transaction amount is 3 standard deviations above average for this client.", // (可选) 更详细的解释
          "timestamp_in_source": "iso_timestamp", // 原始交易时间
          "key_features": { // (可选) 导致异常的关键特征及其值
            "Amount": 150000,
            "HourOfDay": 3
          },
          // ... 其他与该交易相关的原始字段或派生特征，按需提供
        },
        // ... more anomalies
      ]
    }
    ```

## 4. 核心应用集成 (Core Application Integration)

### 4.1. 新模型提议 (Proposed New Models in Core App)
为支持交易异常检测功能，核心审计系统（`audit_management` app）需要新增以下Django模型：

*   **`TransactionDataset`** (交易数据集)
    *   已在 `2.2. 数据接入点` 中详细描述。
    *   关键字段: `project` (FK to AuditProject), `name`, `source_description`, `data_location_uri`, `record_count`, `data_schema_info`, `status` ('New', 'Uploading', 'Uploaded', 'QueuedForAI', 'AIProcessing', 'Analyzed', 'AIError'), `created_at`, `uploaded_by`。

*   **`AnomalyDetectionRun`** (异常检测运行记录)
    *   用于追踪每次AI检测任务的执行情况。
    *   字段:
        *   `id` (UUID, PK)
        *   `project` (ForeignKey to AuditProject): 关联的审计项目。
        *   `dataset` (ForeignKey to TransactionDataset): 关联的交易数据集。
        *   `ai_detection_run_id` (CharField, max_length=255, unique=True, nullable=True): AI服务返回的运行ID。
        *   `status` (CharField): 从AI服务同步的状态 (e.g., 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')。
        *   `sensitivity_level` (CharField, nullable): 本次运行时用户选择的敏感度。
        *   `parameters_used` (JSONField, nullable): 本次运行时使用的具体AI参数。
        *   `summary_info` (JSONField, nullable): 从AI服务获取的摘要结果（如总处理数，发现异常数）。
        *   `ai_results_reference_id` (CharField, nullable): AI服务返回的用于获取详细结果的ID。
        *   `requested_by` (ForeignKey to User): 发起此次检测的用户。
        *   `requested_at` (DateTimeField, auto_now_add=True): 请求发起时间。
        *   `processing_started_at` (DateTimeField, nullable): AI处理开始时间。
        *   `completed_at` (DateTimeField, nullable): AI处理完成时间。
        *   `error_message` (TextField, nullable): 如果AI处理失败，记录错误信息。

*   **`DetectedAnomaly`** (已检测到的异常)
    *   存储AI服务识别出的每一条异常记录的详细信息及审计师的跟进状态。
    *   字段:
        *   `id` (UUID, PK)
        *   `detection_run` (ForeignKey to AnomalyDetectionRun): 关联的检测运行实例。
        *   `transaction_identifier_in_source` (CharField, max_length=512): 在原始数据源中唯一标识该交易的ID或组合键。
        *   `anomaly_score` (FloatField, nullable): AI模型给出的异常度评分。
        *   `ai_suggested_reason_codes` (JSONField, nullable): AI模型提供的简要原因代码列表。
        *   `ai_explanation` (TextField, nullable): AI模型提供的详细解释。
        *   `raw_transaction_details_preview` (JSONField, nullable): (可选) 原始交易中的部分关键字段快照。
        *   `status` (CharField): 审计师处理状态 ('New', 'UnderReview', 'FalsePositive', 'ActionRequired', 'Escalated', 'Closed'). Default: 'New'.
        *   `auditor_notes` (TextField, blank=True, null=True): 审计师对此异常的备注和分析。
        *   `assigned_to_auditor` (ForeignKey to User, null=True, blank=True, related_name='assigned_anomalies'): 分配给负责跟进此异常的审计师。
        *   `created_at` (DateTimeField, auto_now_add=True): 此记录在核心系统中创建的时间。
        *   `updated_at` (DateTimeField, auto_now=True): 此记录的更新时间。

### 4.2. 用户交互流程 (User Interaction Flow - High Level)
1.  **数据准备与关联**:
    *   审计师在核心系统的某个 `AuditProject` 下，通过界面操作“上传”交易数据文件（例如CSV）或“关联”一个已存在的外部数据源。
    *   核心系统创建一个 `TransactionDataset` 记录，存储元数据。如果涉及文件上传，文件将被传输到预定义的对象存储，`data_location_uri` 记录其路径。
2.  **触发检测**:
    *   审计师选择一个状态为 'Uploaded' 的 `TransactionDataset`。
    *   点击“开始异常检测”按钮，可能会被要求选择敏感度或其他参数。
    *   核心应用向AI检测服务的 `POST /api/ai/transaction-anomaly/detect` 端点发起请求，请求体包含 `transaction_dataset_id` 及其 `data_location_uri` 等信息。
    *   核心应用创建一个 `AnomalyDetectionRun` 记录，初始状态为 'PENDING'，并保存AI服务返回的 `ai_detection_run_id`。
3.  **状态跟踪与结果获取**:
    *   核心应用通过后台任务（如Celery worker）定期调用AI服务的 `GET /api/ai/transaction-anomaly/runs/{ai_detection_run_id}` 端点，轮询检测状态。
    *   或者，AI服务在处理完成后，通过回调接口（需额外设计）通知核心应用。
    *   核心应用根据AI服务返回的状态和摘要信息，更新对应的 `AnomalyDetectionRun` 记录。
4.  **结果展示与处理**:
    *   当 `AnomalyDetectionRun` 状态变为 'COMPLETED' 时，核心应用调用AI服务的 `GET /api/ai/transaction-anomaly/results/{results_reference_id}/anomalies` 端点，分批获取详细的异常列表。
    *   获取到的每条异常数据，在核心系统中创建一条 `DetectedAnomaly` 记录，并与相应的 `AnomalyDetectionRun` 关联。
    *   审计师在项目中查看 `DetectedAnomaly` 列表，可以进行筛选、排序、查看详情、添加备注、标记状态（如“误报”、“待跟进”）、分配给其他审计师等。

### 4.3. 界面考虑 (UI Considerations - High Level)
*   **`TransactionDataset` 管理界面**:
    *   列表展示与项目关联的所有数据集及其状态。
    *   提供“上传新数据集”（表单包含名称、描述、文件选择）或“关联外部数据源”（更复杂的表单）的功能。
    *   显示数据集的元数据详情。
    *   操作按钮：触发异常检测、删除数据集（如果允许）、查看关联的检测运行记录。
*   **`AnomalyDetectionRun` 状态展示界面**:
    *   列表展示特定数据集或项目的所有检测运行记录。
    *   显示每次运行的状态、请求者、时间、参数、摘要结果等。
    *   如果失败，显示错误信息。
    *   链接到详细的异常结果列表。
*   **`DetectedAnomaly` 结果处理界面**:
    *   表格形式展示检测到的异常列表，支持分页、排序（按异常分数、交易日期等）、高级筛选（按状态、分配人、分数范围等）。
    *   点击单条异常可查看详细信息（包括AI提供的解释、原始交易快照）。
    *   提供编辑功能，允许审计师修改异常状态、添加备注、分配给团队成员。
    *   (未来) 可能提供批量处理功能（如批量标记为误报）。

## 5. 未来考虑与挑战 (Future Considerations & Challenges)

*   **真实数据的复杂性与多样性**: 实际客户数据可能非常混乱，包含各种格式、错误和不一致性。数据清洗和预处理的鲁棒性至关重要。
*   **模型持续训练与更新**:
    *   需要建立机制来收集审计师对异常的反馈（例如，哪些是真正的异常，哪些是误报）。
    *   利用这些反馈定期重新训练或微调AI模型，以提高其准确性和适应性。
    *   模型版本管理和部署策略。
*   **结果解释与误报处理**:
    *   AI模型（尤其是复杂模型）的“黑盒”特性可能使得结果难以解释。需要探索可解释AI（XAI）技术。
    *   有效处理和减少误报，避免“告警疲劳”，是提升用户信任度和功能实用性的关键。
*   **可扩展性与性能**:
    *   AI检测服务需要能够处理大规模数据集，并在合理时间内返回结果。这可能涉及分布式计算（如Spark）、优化的数据处理库和高效的模型推理。
    *   核心系统在获取和展示大量异常结果时也需要考虑性能。
*   **安全性与隐私**:
    *   交易数据通常高度敏感。在数据传输、存储和处理过程中必须确保最高级别的数据安全和隐私保护，符合相关法规（如GDPR, CCPA, PIPL）。
    *   AI服务访问数据的方式需要严格控制权限。
*   **回调机制设计**: 对于长时间运行的AI任务，除了轮询，设计一个稳健的回调机制（AI服务通知核心应用任务完成）会更高效。
*   **用户体验与信任**: 简洁直观的界面、清晰的结果展示、以及对AI能力边界的透明沟通，对于用户接受和有效使用此功能非常重要。

本文档为“交易异常检测”AI功能的集成提供了初步的框架和方向。随着项目的进展，具体细节将需要进一步细化和迭代。
