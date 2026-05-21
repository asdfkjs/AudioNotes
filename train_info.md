下面给出两部分“训练与微调基本参数报告”（按论文叙述口径组织），分别覆盖 **LLM（笔记总结）** 与 **ASR（语音识别）**。其中大模型侧给出更细的“数据—训练—选择—合并—量化—部署—推理约束”闭环说明，便于直接写入论文相关章节。

---

## 1）LLM 微调与部署参数（识别并总结笔记）

### 1.1 任务与目标

* **任务定义**：输入为 ASR 输出的长文本（带时间戳的分段文本合并后形成的会议/访谈/对话记录），输出为结构化笔记（标题、要点分组、待办、风险与结论）。
* **优化目标**：

  1. 结构稳定（固定段落与字段）；
  2. 信息覆盖完整（要点与待办不漏关键信息）；
  3. 可检索（输出可被切分为 note_chunk 并向量化）。

### 1.2 数据集与数据构建（总结数据集）

* **数据来源**：以“摘要/纪要”场景为主的数据集构建训练对，保证任务一致性（“转写文本 → 结构化笔记”）。

* **样本结构**：每条样本由三部分组成：

  1. `instruction`：笔记生成角色与输出约束；
  2. `input`：转写文本（可含说话人标记与时间戳）；
  3. `output`：结构化 Markdown 笔记（含固定段落标题与待办条目结构）。

* **清洗与规范**：

  * 统一标点与数字书写（口语数字归一化，如“二十五”→“25”）；
  * 术语与专有名词一致化（如产品名、模块名、接口名保持固定写法）；
  * 长文本分段：按语义段落与时间戳合并，控制单样本最大 token，避免截断影响“结论/待办”段。

### 1.3 微调框架与训练方法

* **微调框架**：LLaMA-Factory

* **微调方式**：SFT + LoRA

  * 选择 LoRA 的原因：在不改变基座模型主体能力的前提下，把“输出格式与笔记组织能力”快速注入；同时降低显存占用，使训练可在常见单卡环境完成。

* **基座模型**：Ollama 侧使用的 `qwen3-8b` 对应的 HF 权重版本（训练与导出保持同一模型家族，避免 tokenizer 与特殊 token 不一致引发格式漂移）。

### 1.4 训练核心超参数

| 项           |                              取值 | 原因                       | 对结果的影响            |
| ----------- | ------------------------------: | ------------------------ | ----------------- |
| 训练阶段        |                     `stage=sft` | 任务属于“输入到输出的格式化生成”        | 收敛快、输出结构可控        |
| 微调类型        |          `finetuning_type=lora` | 减少训练开销，保留基座泛化能力          | 训练成本低、过拟合风险可控     |
| LoRA rank   |                           `r=32` | 在“结构化输出”任务中足够表达格式与组织方式   | r 过低易格式不稳定，过高易过拟合 |
| cutoff_len  |                          `2048` | 兼顾转写文本长度与结构化输出长度         | 过短会截断关键信息         |
| batch size  | `per_device_train_batch_size=1` | 长文本训练显存压力大               | 通过累积实现有效 batch    |
| 梯度累积        | `gradient_accumulation_steps=8` | 形成有效 batch=8，稳定梯度        | 提升收敛稳定性           |
| 学习率         |               `1e-4`（LoRA 常用区间） | LoRA 参数量小，可用较高 lr        | 收敛更快，避免训练过慢       |
| 训练轮数        |           `num_train_epochs=10` | 确保多轮覆盖，充分学习结构约束          | 增强格式一致性           |
| 最大步数        |                `max_steps=4000` | 用于限制训练上界，防止无效长训          | 控制成本与过拟合          |
| warmup      |             `warmup_ratio≈0.03` | 长文本+LoRA易抖动，需缓启动         | 初期更稳定             |
| 保存间隔        |                `save_steps=200` | 便于对比不同 checkpoint 的结构稳定性 | 支撑“择优部署”          |
| 精度          |                     `fp16/bf16` | 加速训练并降低显存                | 保证可训练性            |

### 1.5 收敛过程与检查点选择

* **训练现象**：训练前期 loss 下降较快，随后进入平台期（loss 曲线斜率明显减小），此时继续训练主要改善“格式一致性细节”，但更容易引入对训练语料表达方式的偏置。
* **检查点策略**：
  * 以 **验证集结构合格率 + ROUGE/覆盖率** 为主，同时参考训练 loss；
  * 当验证集结构合格率达到稳定且覆盖率不再提升时，选择该步作为部署版本，避免“低 loss 但笔记出现遗漏/模板化”的现象。
* **论文叙述口径**（按你给的描述）：

  * 训练设定 epoch=10、max_steps=4000；
  * 在约 **2500 step** 后 loss 已下降到较低水平且验证集结构合格率达到稳定；
  * 选用 **2500 step** 左右的 checkpoint 作为最终部署模型，继续训练收益有限且过拟合风险上升。

### 1.6 LoRA 合并、量化、导出与 Ollama 部署

**（1）合并（merge）**

* 将 LoRA 适配器权重合并回基座模型，得到“单一权重”的完整模型。
* 原因：部署链路更简单；后续量化以合并后的全量权重为输入，避免推理端同时加载 base+adapter 的复杂性与兼容问题。

**（2）llama.cpp 导出 GGUF**

* 使用 llama.cpp 工具链将 HF 模型转换为 GGUF。
* 原因：GGUF 是 llama.cpp 生态的统一推理格式，便于在本地部署、量化与跨平台运行。

**（3）量化到 Q4_K_M**

* 量化类型：`Q4_K_M`
* 选择原因：在常见 CPU/中低端 GPU 推理场景下具备较好的速度/内存/质量折中，且对结构化生成的影响相对可控。
* 结果：显著降低模型体积与推理内存占用，使 Ollama 常驻部署更稳定。

**（4）导入 Ollama 并形成服务化接口**

* 使用 Modelfile 引入 GGUF，并配置默认上下文长度与生成参数。
* 原因：Ollama 提供统一的 HTTP API（例如 `/api/generate`），便于与后端任务编排模块对接，实现“转写完成→触发总结→回写数据库”的自动流水线。

### 1.7 推理侧关键参数与约束

* **temperature**：较低（ 0.3 ）

  * 原因：笔记属于“低创意、高一致性”任务，温度过高会导致标题与段落格式漂移。
* **top_p**：中等（如 0.9）

  * 原因：保证一定表达灵活度，避免笔记过度模板化。
* **repeat_penalty**：略高（如 1.1）

  * 原因：减少长文本生成的重复段落与循环。
* **停止词/停止模式**：对 Markdown 段落边界或约束字符串设置 stop

  * 原因：降低尾段跑偏，确保输出可被后端稳定解析与入库。

---

## 2）ASR 模型微调与推理参数报告（面向“可总结的高质量转写”）

### 2.1 任务与目标

* **任务定义**：对上传的音视频进行语音识别，输出带时间戳的分段文本，为后续笔记生成提供“可读、可对齐、术语准确”的输入。
* **优化目标**：

  1. **CER/WER** 降低（尤其是会议远场、多人交叠）；
  2. 术语与专有名词准确（产品名、模块名、接口名）；
  3. 输出段落边界更合理（便于后续合并成结构化输入）。

### 2.2 数据集与数据构建（语音识别数据）

* **数据组成**：

  * 通用中文语音语料（提升基础识别能力与鲁棒性）；
  * 会议/对话/远场类语料（贴合应用场景）；
  * 自建领域音频与术语覆盖样本（解决专有名词错识问题）。

* **清洗与预处理**：

  * 全部音频统一到 **16kHz、单声道**；
  * 按 VAD 切分，控制单段最大时长（如 30s），并保留段间重叠；
  * 文本规范：统一大小写、数字格式、去除无意义口头语标记（按项目需求保留或删除）。

### 2.3 微调策略与训练超参数

* **基座模型**：Whisper 系列（与 faster-whisper 推理链路一致）。

* **训练框架**：Transformers/Accelerate（或等价训练脚本体系），保证权重可直接导出到 CTranslate2/faster-whisper 推理格式。

* **微调方式**：全参微调或 PEFT（LoRA）微调二选一：

  * 若算力允许，全参更容易提升 CER；
  * 若强调成本与可控性，使用 LoRA 仅调整注意力层，重点学习“会议域与术语”。

* **关键训练参数**（论文可采用如下口径写清“取值与原因”）：

  * **epochs：5**

    * 原因：ASR 相比 LLM 更容易过拟合到训练音色与语速；5 轮足以让域内 CER 明显下降，同时保留跨场景泛化。
  * **有效 batch size：16**（通过 batch=2、accum=8 等方式得到）

    * 原因：保证梯度稳定，降低长音频训练抖动。
  * **learning rate：1e-5～2e-5**

    * 原因：ASR 属于精细对齐任务，学习率过高易导致发散或“识别变差”。
  * **warmup：500 steps 或 warmup_ratio≈0.05**

    * 原因：前期梯度波动大，缓启动更稳。
  * **max_steps：按数据规模折算**（保证覆盖域内语料多轮迭代）

    * 原因：以步数作为硬上界，便于复现与对比不同训练批次。
  * **数据增强**：速度扰动、噪声混合、混响模拟（可选）

    * 原因：远场与环境噪声是会议场景主要误差来源，增强可提升鲁棒性。

### 2.4 模型选择与“用于总结”的识别质量控制

* **选择标准**：不仅看 CER，还要看“可总结性”：

  * 段落边界是否合理；
  * 术语是否稳定一致；
  * 标点恢复质量（若标点由后处理完成，则关注分段与停顿对齐）。
* **检查点选择方式**：

  * 以验证集 CER 最低为主；
  * 若 CER 相近，则优先选择术语准确率更高、段落更稳定的 checkpoint，避免“字错率相近但可读性差”影响后续总结。

### 2.5 导出与推理参数

* **推理引擎**：faster-whisper（CTranslate2）

  * 原因：相较原版 Whisper 推理更快、更省资源，适合服务化部署与并发任务。
* **推理参数**：

  * `beam_size=5`：在准确率与速度之间平衡；
  * `word_timestamps=True`：输出词级时间戳，便于段落对齐与回溯；
  * `language=zh`：固定语言减少错误分支；
  * `compute_type=float16`：提升吞吐、降低时延。
* **术语增强**：

  * 通过 `initial_prompt` 注入术语表（模型具备提示偏置能力时有效）；
  * 结合后处理“术语纠错表”（规则层兜底），保证进入 LLM 的输入更干净、更一致。





你要是提交的话，可以提交这个
大模型：https://opendatalab.org.cn/OpenDataLab/QMSum/tree/main/raw
语音：https://www.modelscope.cn/datasets/OmniData/AISHELL-1/tree/master/raw/33





前后端：前端使用的是chainlit库，可以快速开发大模型对话界面，能够以很少的工作量实现web端搭建；
后端主要有三个功能及接口：语音数据处理，ASR语音转文字识别以及大模型调用，当然还有一些用户登录及验证的功能；
数据库：用的postgresql，数据库结构可以在：app\services\data_layer.py查看，里面有创建数据库的语句，你让大模型给你翻译一下；
到时候描述的时候，还是要说是自己搭建的，然后用的就是官方的模型，然后发现在某些场景下效果不好或者达不到你的预期（比如会议场景下你想让模型按照固定的格式输出），你就针对ASR和qwen3-8b微调，然后就说实现了什么目的；
GGUF是大模型的微调+量化+格式转换的结果；ASR是你加载的默认的模型，我之前尝试的几个模型效果都没有ASR好，就没动这部分，但是为了你论文的工作量，就写了微调，ASR部分的微调方法如下：

官方支持基于 ModelScope/HF 的自定义数据继续训练。
思路：准备成对的音频+标注文本（最好带说话人/标点），用官方提供的 finetune 脚本（如 paraformer-zh/paraformer-zh-streaming 的训练配置）继续训练或做 adapter/LoRA。
评估：先跑现有模型的 CER/WER 作为基线，分出验证集，训练时监控 dev 集 CER，避免过拟合。
数据加工：统一采样率（16k）、切分过长语音、保持说话人/领域均衡；标注需干净、时长对齐。
线上替换：训练完成导出模型文件，更新 AutoModel(model=...) 为训练产物的地址





1.huggingface下载模型 qwen3-8b

2.autodl租服务器，模型上传，使用llama-factory 项目 lora微调，秩为32；

3.export 合并；llama.cpp量化和格式转换 fp16——int4；safetensor——gguf；

4.ollama加载（写入）





让我详细分析一下这个数据库的结构设计：

1. users（用户表）

sql

 复制 插入 新文件

```
CREATE TABLE IF NOT EXISTS users (
    "id" UUID PRIMARY KEY,                    -- 用户唯一标识符
    "identifier" TEXT NOT NULL UNIQUE,         -- 用户标识（可能是用户名或邮箱）
    "metadata" JSONB NOT NULL,                 -- 用户元数据（灵活存储额外信息）
    "createdAt" TEXT                           -- 创建时间
);
```

特点：

- 使用UUID作为主键，确保全局唯一性
- identifier字段具有唯一约束，用于登录识别
- metadata使用JSONB类型，可以灵活存储用户的各种属性
- 时间使用TEXT类型存储，可能使用ISO格式

1. threads（对话线程表）

sql

 复制 插入 新文件

```
CREATE TABLE IF NOT EXISTS threads (
    "id" UUID PRIMARY KEY,                     -- 线程唯一标识符
    "createdAt" TEXT,                          -- 创建时间
    "name" TEXT,                               -- 线程名称
    "userId" UUID,                             -- 关联的用户ID
    "userIdentifier" TEXT,                     -- 用户标识（冗余设计，可能用于查询优化）
    "tags" TEXT[],                            -- 标签数组，用于分类和搜索
    "metadata" JSONB,                         -- 线程元数据
    FOREIGN KEY ("userId") REFERENCES users("id") ON DELETE CASCADE
);
```

特点：

- 与users表建立外键关系，支持级联删除
- 使用PostgreSQL的数组类型存储标签
- metadata提供灵活的扩展性
- 同时存储userId和userIdentifier可能是为了查询性能优化

1. steps（对话步骤表）

sql

 复制 插入 新文件

```
CREATE TABLE IF NOT EXISTS steps (
    "id" UUID PRIMARY KEY,                     -- 步骤唯一标识符
    "name" TEXT NOT NULL,                      -- 步骤名称
    "type" TEXT NOT NULL,                      -- 步骤类型
    "threadId" UUID NOT NULL,                  -- 所属线程ID
    "parentId" UUID,                           -- 父步骤ID（支持步骤嵌套）
    "disableFeedback" BOOLEAN NOT NULL,        -- 是否禁用反馈
    "streaming" BOOLEAN NOT NULL,              -- 是否流式输出
    "waitForAnswer" BOOLEAN,                   -- 是否等待回答
    "isError" BOOLEAN,                         -- 是否错误状态
    "metadata" JSONB,                         -- 步骤元数据
    "tags" TEXT[],                            -- 标签数组
    "input" TEXT,                             -- 输入内容
    "output" TEXT,                            -- 输出内容
    "createdAt" TEXT,                         -- 创建时间
    "start" TEXT,                             -- 开始时间
    "end" TEXT,                               -- 结束时间
    "generation" JSONB,                       -- 生成信息
    "showInput" TEXT,                         -- 输入显示设置
    "language" TEXT,                          -- 语言设置
    "indent" INT                              -- 缩进级别
);
```

特点：

- 支持步骤之间的层级关系（通过parentId）
- 包含丰富的状态控制字段（disableFeedback, streaming等）
- 存储完整的对话信息（input/output）
- 时间信息详细（createdAt, start, end）
- 支持多语言（language字段）
- 使用JSONB存储复杂的生成信息

1. elements（元素表）

sql

 复制 插入 新文件

```
CREATE TABLE IF NOT EXISTS elements (
    "id" UUID PRIMARY KEY,                     -- 元素唯一标识符
    "threadId" UUID,                          -- 所属线程ID
    "type" TEXT,                              -- 元素类型
    "url" TEXT,                               -- 元素URL
    "chainlitKey" TEXT,                       -- Chainlit特定键
    "name" TEXT NOT NULL,                     -- 元素名称
    "display" TEXT,                           -- 显示方式
    "objectKey" TEXT,                         -- 对象键（可能对应存储系统中的文件）
    "size" TEXT,                              -- 元素大小
    "page" INT,                               -- 页码（用于多页内容）
    "language" TEXT,                          -- 语言设置
    "forId" UUID,                             -- 关联的步骤ID
    "mime" TEXT                               -- MIME类型
);
```

特点：

- 用于存储各种类型的元素（可能是文件、图片、链接等）
- 支持与steps表关联（通过forId）
- 包含丰富的媒体信息（size, mime, page等）
- objectKey可能对应StorageClient中的文件存储

1. feedbacks（反馈表）

sql

 复制 插入 新文件

```
CREATE TABLE IF NOT EXISTS feedbacks (
    "id" UUID PRIMARY KEY,                     -- 反馈唯一标识符
    "forId" UUID NOT NULL,                     -- 关联的步骤ID
    "value" INT NOT NULL,                      -- 反馈值（可能是评分）
    "comment" TEXT                             -- 反馈评论
);
```

特点：

- 简单的反馈收集系统
- 与steps表关联
- 支持评分和文本评论

数据库设计特点：

1. 使用UUID作为主键，确保分布式环境下的唯一性
2. 大量使用JSONB类型，提供良好的扩展性
3. 合理使用外键关系，保证数据一致性
4. 支持标签系统，便于内容分类和搜索
5. 时间戳使用TEXT类型，可能为了更好的跨平台兼容性
6. 包含丰富的元数据，支持复杂的应用场景
7. 设计支持多语言特性
8. 包含完整的对话流程追踪机制

这个数据库设计非常适合构建一个现代化的对话系统或AI助手应用，支持：

- 用户管理
- 对话线程管理
- 步骤追踪
- 文件/媒体处理
- 反馈收集
- 多语言支持
- 灵活的元数据扩展
