# 审计项目管理系统架构设计文档

## 1. 引言 (Introduction)
本文档旨在详细阐述审计项目管理系统的架构设计，为系统的开发、部署和维护提供蓝图和指导。
架构目标是构建一个现代化、可扩展、安全、且易于集成AI功能的审计管理平台，确保系统能够高效支持当前及未来的审计业务需求。

## 2. 技术选型 (Technology Stack)

*   **后端 (Backend):** Python (Django框架)
    *   **理由:** Python拥有成熟且强大的AI/ML生态系统 (如Scikit-learn, TensorFlow, PyTorch)，便于集成AI功能。Django框架提供了快速开发、ORM、自带管理后台等特性，能提高开发效率。社区支持广泛，拥有大量成熟的第三方库。
*   **前端 (Frontend):** React
    *   **理由:** React是目前最流行的前端框架之一，采用组件化开发模式，拥有庞大的社区和丰富的生态系统。通过虚拟DOM提供高性能的用户体验。具体UI库（如Ant Design, Material-UI）可在UI设计阶段进一步评估。
*   **数据库 (Database):** PostgreSQL
    *   **理由:** PostgreSQL是一款功能强大、稳定可靠的开源对象-关系型数据库系统。支持复杂的SQL查询、事务处理（ACID特性）、JSONB字段、全文搜索以及良好的扩展性，能够满足审计系统对数据一致性和复杂性的要求。
*   **AI/ML:** Python生态 (Scikit-learn, TensorFlow, PyTorch)
    *   **理由:** 这是AI/ML领域的行业标准，提供了丰富的算法库、预训练模型和数据处理工具，能够支持从传统机器学习到深度学习的各种AI应用。
*   **部署 (Deployment):** Docker (容器化), Kubernetes (容器编排)
    *   **理由:** Docker实现应用程序的标准化打包和隔离，确保开发、测试和生产环境的一致性。Kubernetes提供强大的容器编排能力，包括自动化部署、弹性伸缩、服务发现和故障恢复。推荐在主流云平台 (如AWS, Azure, 阿里云等) 部署，以利用其托管的Kubernetes服务和其它基础设施。

## 3. 系统架构 (System Architecture)

### 3.1. 架构风格 (Architectural Style)
采用**面向服务的架构 (SOA)** 作为基础，并具备向**微服务架构 (Microservices Architecture)** 平滑演进的能力。
核心业务逻辑将封装在独立的服务中，服务之间通过明确定义的API进行通信。AI功能将作为独立的或半独立的服务模块进行构建和部署，以保证其灵活性和可独立扩展性。这种方式有利于模块化开发、独立部署和技术栈的灵活选择。

### 3.2. 高层架构图描述 (High-Level Architecture Diagram Description)
系统将分层设计，主要包括用户接口层、应用服务层、数据存储层和基础设施与支撑服务。

*   **用户接口层 (User Interface Layer):**
    *   **Web应用 (Web Application):** 基于React构建的单页应用 (SPA)，提供丰富的用户交互和审计业务操作界面。
    *   **(未来) 移动应用接口 (Mobile App API):** 为未来的移动端应用预留API接口，方便审计人员在移动设备上进行操作。

*   **应用服务层 (Application Service Layer):**
    *   **API网关 (API Gateway):** (例如 Kong, Nginx Plus, 或云厂商提供的API Gateway服务)
        *   **功能:** 作为系统的统一入口，处理所有客户端请求。负责请求路由、负载均衡、身份认证与授权（集成认证服务）、API限流、日志记录、监控和安全策略实施。
    *   **核心审计服务 (Core Audit Service):** (Python - Django)
        *   **功能:** 实现审计项目管理（计划、立项、审批）、任务分配与跟踪、审计程序管理、工作底稿编制与复核、审计发现记录与整改跟踪、用户角色与权限管理等核心业务逻辑。通过RESTful API对外提供服务。
    *   **AI服务 (AI Services):** (Python - FastAPI 或 Flask，结合AI框架)
        *   **功能:** 作为独立的服务模块，提供AI驱动的功能。每个AI功能可以是一个或一组微服务。
            *   **风险评估服务 (Risk Assessment Service):** 分析数据，识别高风险审计领域。
            *   **交易异常检测服务 (Anomaly Detection Service):** 监测交易数据，发现异常模式。
            *   **自动化合规检查服务 (Automated Compliance Check Service):** NLP辅助检查文档与法规的符合性。
            *   **智能资源分配建议服务 (Intelligent Resource Allocation Service):** 辅助审计经理进行人员调配。
            *   **预测性审计发现服务 (Predictive Audit Findings Service):** 预测潜在审计问题。
        *   **交互方式:** 通过RESTful API与核心审计服务或其他服务交互。
    *   **通知服务 (Notification Service):** (可基于现有消息队列实现，或使用专用通知服务如SendGrid)
        *   **功能:** 负责处理系统内的各类通知，如邮件提醒、站内消息、App推送（未来）等。

*   **数据存储层 (Data Storage Layer):**
    *   **主数据库 (Primary Database):** PostgreSQL
        *   **功能:** 存储结构化的核心业务数据，如项目信息、用户信息、审计发现、任务状态等。采用主从复制架构保证高可用性。
    *   **文档/对象存储 (Document/Object Storage):** (例如 MinIO (自建), AWS S3, Azure Blob Storage, 阿里云OSS)
        *   **功能:** 存储非结构化的审计证据文件（如PDF, Word, Excel, 图片, 音视频）、审计报告、系统文档等。
    *   **AI数据/模型存储 (AI Data/Model Storage):** (可能使用文件系统、对象存储或专用模型仓库如MLflow)
        *   **功能:** 存储AI模型训练所需的数据集、预处理脚本、训练好的模型文件及版本信息。
    *   **缓存服务 (Caching Service):** (例如 Redis, Memcached)
        *   **功能:** 缓存热点数据（如用户会话、权限信息、常用配置）、API响应结果，以减少数据库压力，提升系统响应速度。

*   **基础设施与支撑服务 (Infrastructure & Supporting Services):**
    *   **认证与授权服务 (Authentication & Authorization Service):** (例如 Keycloak (自建), Auth0, Okta, 或集成企业现有LDAP/OAuth2/OIDC身份提供商)
        *   **功能:** 负责用户身份认证、单点登录 (SSO)、令牌管理以及细粒度的权限控制。API网关将与此服务集成。
    *   **消息队列 (Message Queue):** (例如 RabbitMQ, Apache Kafka)
        *   **功能:** 用于服务间的异步通信和任务解耦。例如，耗时的AI分析任务、报告生成、批量通知等可以通过消息队列异步处理，提高系统响应能力和韧性。
    *   **日志管理 (Logging):** (例如 ELK Stack - Elasticsearch, Logstash, Kibana; 或 EFK Stack - Elasticsearch, Fluentd, Kibana)
        *   **功能:** 集中收集、存储、搜索和分析来自所有服务和组件的日志，便于问题排查、系统监控和安全审计。
    *   **监控与告警 (Monitoring & Alerting):** (例如 Prometheus + Grafana, Zabbix, 或云厂商监控服务)
        *   **功能:** 监控系统各组件的性能指标（CPU、内存、磁盘、网络、响应时间、错误率等）、业务指标，并在发生故障或达到预警阈值时发送告警。
    *   **CI/CD管道 (CI/CD Pipeline):** (例如 Jenkins, GitLab CI/CD, GitHub Actions, Azure DevOps)
        *   **功能:** 自动化代码构建、单元测试、集成测试、安全扫描、打包和部署流程，实现快速、可靠的软件交付。

## 4. 数据模型初步设计 (Initial Data Model Design)
以下为核心业务实体及其关键属性的初步设计，详细设计将在数据库设计阶段完成。

*   **`Projects` (审计项目)**
    *   `project_id` (PK, 项目ID)
    *   `project_name` (项目名称)
    *   `project_code` (项目编号, 唯一)
    *   `scope` (审计范围)
    *   `objectives` (审计目标)
    *   `lead_auditor_id` (FK, 项目负责人/主审)
    *   `manager_id` (FK, 审计经理)
    *   `status` (状态: 计划中, 进行中, 复核中, 已完成, 已归档)
    *   `start_date` (计划开始日期)
    *   `end_date` (计划结束日期)
    *   `actual_start_date` (实际开始日期)
    *   `actual_end_date` (实际结束日期)
    *   `risk_level` (风险等级)
    *   `created_at`, `updated_at`

*   **`Tasks` (审计任务)**
    *   `task_id` (PK, 任务ID)
    *   `project_id` (FK, 所属项目ID)
    *   `parent_task_id` (FK, 父任务ID, 支持任务分解)
    *   `task_name` (任务名称)
    *   `description` (任务描述/审计程序)
    *   `assigned_to_id` (FK, 分配给的用户ID)
    *   `status` (状态: 未开始, 进行中, 待复核, 已完成)
    *   `due_date` (截止日期)
    *   `priority` (优先级)
    *   `created_at`, `updated_at`

*   **`Users` (用户)**
    *   `user_id` (PK, 用户ID)
    *   `username` (用户名, 唯一)
    *   `password_hash` (密码哈希)
    *   `email` (邮箱, 唯一)
    *   `full_name` (姓名)
    *   `role_id` (FK, 角色ID)
    *   `is_active` (是否激活)
    *   `last_login_at` (最后登录时间)
    *   `created_at`, `updated_at`

*   **`Roles` (角色)**
    *   `role_id` (PK, 角色ID)
    *   `role_name` (角色名称: 管理员, 审计经理, 主审, 审计师, 被审计用户等)
    *   `description` (角色描述)
    *   `permissions` (JSONB, 权限列表)

*   **`Findings` (审计发现)**
    *   `finding_id` (PK, 发现ID)
    *   `project_id` (FK, 所属项目ID)
    *   `task_id` (FK, 关联任务ID)
    *   `title` (发现标题)
    *   `description` (详细描述)
    *   `criteria` (判断标准)
    *   `impact` (潜在影响)
    *   `recommendation` (审计建议)
    *   `severity` (严重性/风险等级: 高, 中, 低)
    *   `status` (状态: 初稿, 待确认, 整改中, 待验证, 已关闭)
    *   `responsible_person_id` (FK, 被审计单位整改责任人)
    *   `due_date_for_remediation` (整改截止日期)
    *   `created_by_id` (FK, 创建人ID)
    *   `created_at`, `updated_at`

*   **`Documents` (审计文档/证据)**
    *   `document_id` (PK, 文档ID)
    *   `related_entity_type` (关联实体类型: Project, Task, Finding)
    *   `related_entity_id` (FK, 关联实体ID)
    *   `file_name` (原始文件名)
    *   `file_type` (文件MIME类型)
    *   `file_size` (文件大小)
    *   `storage_path` (存储路径/对象存储Key)
    *   `version` (版本号)
    *   `uploaded_by_id` (FK, 上传者ID)
    *   `created_at`, `updated_at`

*   **`AuditLogs` (审计日志/操作日志)**
    *   `log_id` (PK, 日志ID)
    *   `user_id` (FK, 操作用户ID, 可为空针对系统操作)
    *   `action_type` (操作类型: 例如 LOGIN, CREATE_PROJECT, UPLOAD_DOCUMENT, UPDATE_FINDING_STATUS)
    *   `target_entity_type` (操作对象类型)
    *   `target_entity_id` (操作对象ID)
    *   `timestamp` (操作时间戳)
    *   `details` (JSONB, 操作详情，如修改前后的值)
    *   `ip_address` (操作者IP地址)

## 5. AI集成策略 (AI Integration Strategy)
*   **服务化部署:** AI模型将封装为独立的服务 (AI Services)，通过轻量级的RESTful API (使用FastAPI或Flask) 对外提供预测或分析能力。
*   **异步调用:** 对于耗时较长的AI分析任务（如大规模数据异常检测、复杂风险模型计算），核心审计服务将通过消息队列异步调用AI服务，避免阻塞主流程。
*   **数据交互:** AI服务可能需要访问主数据库的只读副本或特定的数据集市进行分析。分析结果将通过API返回或写入指定的数据表。
*   **模型版本管理:** 实施AI模型版本控制策略，确保模型的可追溯性和可重复性。考虑使用MLflow等工具管理模型生命周期。
*   **持续训练与监控:** 建立AI模型性能监控机制，并根据新的数据和反馈定期对模型进行重新训练和优化，以保持其准确性和有效性。

## 6. 部署策略 (Deployment Strategy)
*   **容器化:** 所有服务（后端应用、前端应用、AI服务、部分支撑服务如Redis）都将被容器化 (使用Docker)。
*   **容器编排:** 使用Kubernetes (K8s) 进行容器的编排和管理，实现自动化部署、弹性伸缩、服务发现、滚动更新和故障自愈。
*   **云平台优先:** 优先考虑在主流云平台 (AWS EKS, Azure AKS, Google GKE, 阿里云ACK) 上部署，充分利用其提供的托管Kubernetes服务、数据库服务、对象存储、监控告警等基础设施，降低运维复杂度。
*   **环境隔离:** 至少维护开发 (Development)、测试 (Testing/Staging) 和生产 (Production) 三套环境，各环境网络隔离，配置独立。
*   **CI/CD:** 建立完善的CI/CD流水线，实现从代码提交到自动化测试、构建Docker镜像、推送到镜像仓库、最终部署到Kubernetes集群的自动化流程。

## 7. 非功能性需求考虑 (Non-Functional Requirements Considerations)

*   **可扩展性 (Scalability):**
    *   **水平扩展:** 核心审计服务和AI服务设计为无状态或准无状态，便于通过Kubernetes进行水平扩展（增加Pod副本数）。
    *   **数据库扩展:** PostgreSQL支持读写分离、分区等策略。
    *   **异步处理:** 利用消息队列处理峰值负载和耗时任务。
*   **可靠性与高可用性 (Reliability & High Availability):**
    *   **服务冗余:** 关键服务在Kubernetes中部署多个副本，避免单点故障。
    *   **数据库高可用:** PostgreSQL采用主从复制或集群方案（如Patroni）。
    *   **数据备份与恢复:** 定期进行数据备份，并制定灾难恢复计划。
    *   **健康检查与自愈:** Kubernetes Liveness 和 Readiness Probes。
*   **安全性 (Security):**
    *   **通信加密:** 全站强制HTTPS (TLS/SSL)。服务间内部通信也应考虑加密。
    *   **认证授权:** API网关集成统一的认证授权服务 (OAuth2/OIDC)，严格控制API访问权限。
    *   **数据加密:** 对数据库中的敏感数据（如密码、个人信息）进行加密存储。考虑对对象存储中的文件进行服务端加密。
    *   **依赖安全:** 定期扫描代码和依赖库，修复已知漏洞。
    *   **安全审计日志:** 记录所有敏感操作。
    *   **最小权限原则:** 各组件和服务仅授予其完成任务所必需的最小权限。
    *   **输入验证与输出编码:** 防范XSS、SQL注入等常见Web攻击。
*   **可维护性 (Maintainability):**
    *   **模块化设计:** 清晰的服务边界和API接口定义。
    *   **代码质量:** 遵循统一的编码规范，进行代码审查，编写单元测试和集成测试。
    *   **文档:** 完善的API文档、架构文档、部署文档和运维手册。
    *   **日志与监控:** 提供充分的日志信息和监控指标，便于问题定位和性能分析。
*   **性能 (Performance):**
    *   **高效查询:** 优化数据库查询，合理使用索引。
    *   **缓存机制:** 有效利用缓存减少延迟。
    *   **异步处理:** 异步执行非核心路径上的耗时操作。
    *   **前端优化:** 代码分割、懒加载、静态资源CDN等。
    *   **压力测试:** 定期进行性能测试和压力测试，识别瓶颈。
