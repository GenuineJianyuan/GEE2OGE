-- ============================================================
-- GEE-OGE 算子映射知识库 - 数据库建表脚本
-- 严格遵循《表结构整理.docx》设计
-- 数据库: SQLite
-- ============================================================

-- 启用外键约束
PRAGMA foreign_keys = ON;

-- ============================================================
-- 表 1: class_mapping (类映射表)
-- GEE 类与 OGE 类的对应关系
-- ============================================================
DROP TABLE IF EXISTS class_mapping;
CREATE TABLE class_mapping (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    gee_class   VARCHAR(50) NOT NULL,          -- GEE 类名，如 ee.Image、ee.FeatureCollection
    oge_class   VARCHAR(50),                   -- OGE 对应类名，如 Coverage、FeatureCollection
    is_valid    BOOLEAN DEFAULT 1,             -- TRUE 表示可映射，FALSE 表示无对应（直接跳过）
    remark      TEXT,                          -- 备注（如 "GEE的Image对应OGE的Coverage"）
    UNIQUE(gee_class)
);

-- ============================================================
-- 表 2: gee_api_info (GEE API 原始信息表)
-- 来自 gee.json 全量 GEE API 元数据
-- ============================================================
DROP TABLE IF EXISTS gee_api_info;
CREATE TABLE gee_api_info (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    api_full_name   VARCHAR(200) NOT NULL UNIQUE,  -- 如 ee.Image.normalizedDifference
    class_name      VARCHAR(50),                   -- 如 ee.Image（关联 class_mapping.gee_class）
    method_name     VARCHAR(100),                  -- 如 normalizedDifference
    return_type     VARCHAR(50),                   -- 如 Image
    arg_types       JSON,                          -- 参数类型列表，如 ["List"]
    arg_count       INTEGER DEFAULT 0,             -- 参数个数（必填+可选）
    description     TEXT,                          -- 官方功能描述
    samplecode      TEXT,                          -- 示例代码（从 examples 提取并删除 // 注释，纯代码）
    sample_source   VARCHAR(20),                   -- 示例来源：example（官方）或 generated（自动生成）
    is_analytical   BOOLEAN DEFAULT 1,             -- 过滤标记。ee.List/ee.Dictionary/ui.* 等设为 FALSE，后续匹配直接跳过
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 表 3: oge_api_info (OGE API 原始信息表)
-- 来自 oge.json 全量 OGE API 元数据
-- ============================================================
DROP TABLE IF EXISTS oge_api_info;
CREATE TABLE oge_api_info (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    oge_id              INTEGER,                       -- OGE 原始业务 ID（oge.json 中的 id 字段）
    api_name            VARCHAR(200) NOT NULL UNIQUE,  -- 如 Coverage.resampInterpByGrass
    catalog_id          INTEGER,                       -- 对应 JSON 中的 catalogId
    catalog_name        VARCHAR(100),                  -- 如 "预处理"、"广西林业模型"
    input_types         JSON,                          -- 解析 definitionJson 得到的输入类型列表，如 ["Coverage","String","String"]
    output_type         VARCHAR(50),                   -- 解析 definitionJson 得到的返回类型，如 Coverage
    description         TEXT,                          -- 功能描述
    is_custom_model     BOOLEAN DEFAULT 0,             -- 第一级过滤：catalogId=117（林业模型）或 type=2（AI模型）设为 TRUE，直接弃用
    is_deprecated       BOOLEAN DEFAULT 0,             -- 第三级过滤：名称含 _deprecated 设为 TRUE，放入低优先级
    is_general_purpose  BOOLEAN DEFAULT 0,             -- 第二级过滤：属于"预处理/单要素/多要素/地形"的设为 TRUE，作为主要候选池
    raw_definition_json JSON,                          -- 保留原始 JSON 字符串，方便回溯审计
    samplecode          TEXT                           -- 算子的示例代码
);

-- ============================================================
-- 表 4: operator_mapping (最终算子映射表)
-- 最终产出：GEE 算子到 OGE 算子/Python 实现的映射关系
-- ============================================================
DROP TABLE IF EXISTS operator_mapping;
CREATE TABLE operator_mapping (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    gee_api_id            INTEGER NOT NULL,                -- 关联 gee_api_info.id
    oge_api_id            INTEGER,                         -- 关联 oge_api_info.id（若为 native_python 或 missing，可置 NULL）
    mapping_type          VARCHAR(20) NOT NULL,            -- 四类：one_to_one、one_to_many、many_to_one、native_python、missing
    combo_steps           JSON,                            -- 仅用于 one_to_many：存储实现步骤
    native_python_code    TEXT,                            -- 仅用于 native_python：存参考 Python 实现
    confidence            DECIMAL(5,4) DEFAULT 0.0000,     -- 最终置信度（0~1），由大模型打分或人工填入
    llm_judge_detail      JSON,                            -- 大模型给出的判定依据
    verification_status   VARCHAR(30) DEFAULT 'pending_review',  -- pending_review、auto_approved、manually_approved、rejected
    review_comment        TEXT,                            -- 校验备注（如"参数顺序需注意"）
    FOREIGN KEY (gee_api_id) REFERENCES gee_api_info(id) ON DELETE CASCADE,
    FOREIGN KEY (oge_api_id) REFERENCES oge_api_info(id) ON DELETE SET NULL
);

-- 校验状态约束（SQLite 使用 CHECK 实现 ENUM 语义）
-- ALTER TABLE operator_mapping ADD CHECK (
--     mapping_type IN ('one_to_one', 'one_to_many', 'many_to_one', 'native_python', 'missing')
-- );
-- ALTER TABLE operator_mapping ADD CHECK (
--     verification_status IN ('pending_review', 'auto_approved', 'manually_approved', 'rejected')
-- );

-- ============================================================
-- 索引
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_gee_class       ON gee_api_info(class_name);
CREATE INDEX IF NOT EXISTS idx_gee_analytical  ON gee_api_info(is_analytical);
CREATE INDEX IF NOT EXISTS idx_oge_catalog     ON oge_api_info(catalog_id);
CREATE INDEX IF NOT EXISTS idx_oge_general     ON oge_api_info(is_general_purpose);
CREATE INDEX IF NOT EXISTS idx_oge_custom      ON oge_api_info(is_custom_model);
CREATE INDEX IF NOT EXISTS idx_mapping_gee     ON operator_mapping(gee_api_id);
CREATE INDEX IF NOT EXISTS idx_mapping_oge     ON operator_mapping(oge_api_id);
CREATE INDEX IF NOT EXISTS idx_mapping_type    ON operator_mapping(mapping_type);

-- ============================================================
-- 表 5: case_study_pipeline (Case Study 流水线记录表)
-- 记录每次执行 case_study 6 步流水线的结果，便于追溯
-- ============================================================
DROP TABLE IF EXISTS case_study_pipeline;
CREATE TABLE case_study_pipeline (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_name       VARCHAR(100),                   -- 案例名称（如 "华东小麦长势监测"）
    gee_code        TEXT,                           -- 原始 GEE 代码
    step1_summary   JSON,                           -- 步骤1: 语义抽象结果
    step2_apis      JSON,                           -- 步骤2: API 需求清单
    step3_match     JSON,                           -- 步骤3: GEE→OGE 匹配结果
    step4_codegen   JSON,                           -- 步骤4: 步骤级 OGE 代码生成结果
    step5_feasible  JSON,                           -- 步骤5: 可行性补全结果
    step6_workflow  TEXT,                           -- 步骤6: 最终 OGE 工作流代码
    match_rate      DECIMAL(5,4),                   -- API 匹配率
    feasibility     VARCHAR(30),                    -- 整体可行性：full_feasible / partial_feasible / infeasible
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 版本管理表（用于知识库版本控制）
-- ============================================================
DROP TABLE IF EXISTS mapping_version;
CREATE TABLE mapping_version (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    version_no      VARCHAR(20) NOT NULL UNIQUE,    -- 版本号，如 v1.0.0
    publish_time    DATETIME DEFAULT CURRENT_TIMESTAMP,
    change_log      TEXT,                           -- 变更说明
    reviewer        VARCHAR(50),                    -- 校验人
    is_active       BOOLEAN DEFAULT 0               -- 当前是否为生效版本
);

-- ============================================================
-- 表 6: test_records (测试记录表)
-- 存储所有接口测试的历史记录
-- ============================================================
DROP TABLE IF EXISTS test_records;
CREATE TABLE test_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    api_id          VARCHAR(50) NOT NULL,           -- 接口ID（如 llm-status, convert）
    api_path        VARCHAR(200) NOT NULL,          -- 接口路径（如 /api/llm-status）
    method          VARCHAR(10) NOT NULL,           -- 请求方法（GET/POST）
    request_params  TEXT,                           -- 请求参数（JSON字符串）
    request_time    DATETIME NOT NULL,              -- 请求时间
    status_code     INTEGER,                        -- 响应状态码（如 200, 404, 500）
    response_time   INTEGER,                        -- 响应耗时（毫秒）
    response_body   TEXT,                           -- 响应体（JSON字符串）
    success         BOOLEAN DEFAULT 0,              -- 是否成功（status_code 200-299）
    error_message   TEXT,                           -- 错误信息（如果有）
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_test_records_api_id ON test_records(api_id);
CREATE INDEX idx_test_records_request_time ON test_records(request_time);
CREATE INDEX idx_test_records_success ON test_records(success);
