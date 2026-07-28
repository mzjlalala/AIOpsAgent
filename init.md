- # 角色

  你是一位拥有15年以上经验的 AI 架构师、Python 高级工程师、LangGraph 核心开发者、DevOps 专家以及 Prompt Engineer。

  你曾参与设计和开发：

  - LangGraph Agent Framework
  - LangChain
  - OpenAI Agents SDK
  - MCP Protocol
  - Kubernetes 运维平台
  - Prometheus/Grafana 监控系统
  - 企业级 AIOps 平台
  - RAG 知识库系统

  请按照真实企业生产系统标准完成项目。

  不要开发 Demo。

  目标：

  打造一个可以写入简历、用于高级后端 / AI Agent 工程师面试展示的企业级项目。

  ----------------------------------------

  # 项目名称

  OpsAgent

  企业级 AI 运维 Agent 平台

  定位：

  基于大语言模型 + Agent Workflow + RAG + MCP 的智能运维系统。

  目标：

  实现：

  - 自动分析线上故障
  - 自动收集监控指标
  - 自动分析日志
  - 查询运维知识库
  - 生成故障根因分析
  - 输出解决方案
  - 支持人工审批后执行自动化操作
  - 自动生成事故复盘报告


  ----------------------------------------

  # 技术栈

  ## 后端

  Python 3.13+

  FastAPI

  Pydantic v2

  SQLAlchemy 2.x

  Alembic


  ## Agent

  LangGraph

  LangChain

  OpenAI SDK

  MCP SDK


  ## 数据

  MySQL 8

  Redis

  Milvus


  ## AI模型

  Qwen

  DeepSeek

  OpenAI

  Claude


  ## 工程

  Docker

  Docker Compose

  Loguru

  httpx

  pytest

  Ruff

  Black

  isort


  ## 通信

  SSE

  WebSocket


  ----------------------------------------

  # 系统整体架构


  Vue3 Web

          |
      
          |

  FastAPI Gateway

          |
      
          |

  Agent Service

          |
      
          +----------------+
      
          |                |
      
       LangGraph        Tools
      
          |                |
      
          |                |

   Multi-Agent        MCP Adapter


          |
      
          |

  Knowledge/RAG


          |
      
          |

  Milvus


          |
      
          |

  MySQL + Redis

  

  ----------------------------------------

  # LLM Provider设计


  设计统一LLM抽象层。

  支持：

  - OpenAI
  - Azure OpenAI
  - Qwen
  - DeepSeek
  - Claude
  - Gemini


  要求：

  禁止业务代码直接调用SDK。

  统一：

  LLMProvider


  例如：


  BaseLLMProvider

          |
      
          |

  DashScopeProvider

  OpenAIProvider

  ClaudeProvider

  

  通过配置切换。

  ----------------------------------------

  # Agent架构


  必须采用 LangGraph。


  禁止简单Chain。


  采用Multi-Agent。


  架构：


  Coordinator Agent

  负责任务分发


          |
      
          |


  Planner Agent

  负责任务规划


          |
      
          |


  Metric Agent

  负责指标分析


          |
      
          |


  Log Agent

  负责日志分析


          |
      
          |


  Knowledge Agent

  负责RAG检索


          |
      
          |


  Executor Agent

  负责执行操作


          |
      
          |


  Reporter Agent

  生成事故报告

  

  ----------------------------------------

  # 核心业务流程


  场景：

  线上服务CPU突然100%。


  流程：


  用户提交问题

  或者

  Prometheus告警触发


  ↓

  Coordinator Agent


  ↓

  Planner Agent


  生成：


  Step1 查询CPU指标

  Step2 查询异常日志

  Step3 查询最近发布记录

  Step4 查询知识库

  Step5 分析根因


  ↓

  Metric Tool


  获取监控数据


  ↓

  Log Tool


  获取日志


  ↓

  Knowledge Tool


  RAG检索


  ↓

  LLM分析


  ↓

  生成：

  Root Cause

  Impact

  Solution


  ↓

  Human Approval


  ↓

  Executor


  ↓

  Reporter


  生成事故报告

  

  ----------------------------------------

  # Tool设计


  所有Tool必须接口化。


  采用Adapter模式。


  例如：


  ## Metric


  BaseMetricTool


      |
      
      |


  MockMetricTool


      |
      
      |

  PrometheusTool


  ----------------------------------------


  ## Log


  BaseLogTool


      |
      
      |

  MockLogTool


      |
      
      |

  AliyunSLSTool


      |
      
      |

  ELKTool


      |
      
      |

  LokiTool

  

  ----------------------------------------


  ## Executor


  BaseExecutor


      |
      
      |

  MockExecutor


      |
      
      |

  KubernetesExecutor


      |
      
      |

  SSHExecutor


      |
      
      |

  DockerExecutor

  

  ----------------------------------------


  第一阶段：

  所有工具使用Mock实现。


  禁止真正执行服务器操作。


  预留生产接口。

  

  ----------------------------------------

  # MCP设计


  系统必须兼容MCP。


  设计：

  MCP Tool Adapter。


  未来支持：


  Prometheus MCP

  Grafana MCP

  Kubernetes MCP

  GitLab MCP

  Linux MCP

  MySQL MCP

  Redis MCP


  Tool调用必须支持：

  本地Tool

  MCP Tool


  统一管理。

  

  ----------------------------------------

  # RAG系统


  必须实现企业级RAG。


  Embedding：

  使用：

  阿里云百炼

  text-embedding-v4


  必须封装：


  EmbeddingProvider


  支持：


  embed_query()


  embed_documents()

  

  ----------------------------------------


  向量数据库：

  生产：

  Milvus


  开发：

  允许FAISS


  ----------------------------------------


  知识来源：


  Runbook

  Markdown

  PDF

  Word

  FAQ

  事故案例


  ----------------------------------------


  RAG流程：


  Document


  ↓

  Loader


  ↓

  Cleaner


  ↓

  Splitter


  ↓

  Embedding(text-embedding-v4)


  ↓

  Milvus


  ↓

  Retriever


  ↓

  Reranker(接口)


  ↓

  LLM


  ----------------------------------------


  支持：


  Chunk


  Metadata


  TopK


  Source Citation


  Document Version


  Hybrid Search(接口预留)


  MMR Retrieval(接口预留)


  Query Rewrite(接口预留)

  

  ----------------------------------------

  # Reranker设计


  必须预留接口。


  设计：


  BaseReranker


      |
      
      |

  NoopReranker


      |
      
      |

  DashScopeReranker


      |
      
      |

  BGEReranker

  

  通过配置开启。


  ----------------------------------------

  # Memory设计


  实现：


  Conversation Memory


  Session Memory


  Long Memory


  Experience Memory

  

  其中：


  短期：

  Redis


  长期：

  Milvus

  

  Experience Memory:

  保存：

  成功案例

  失败案例

  处理方案

  

  用于后续Agent学习。

  

  ----------------------------------------

  # Workflow设计


  采用：

  Plan Execute模式。


  Planner输出：


  [
   Step1,
   Step2,
   Step3
  ]


  Executor逐步执行。


  要求支持：

  Retry

  Timeout

  Fallback

  Checkpoint

  Human Approval

  

  ----------------------------------------

  # Reflection机制


  Agent执行完成后。


  Reflection Agent分析：


  - 哪一步失败
  - Tool耗时
  - LLM耗时
  - 是否需要优化


  结果保存：

  Experience Memory。

  

  ----------------------------------------

  # Agent Observability


  必须实现。


  记录：


  Agent执行链路

  Node耗时

  Tool耗时

  LLM耗时

  Token消耗

  异常信息


  类似：

  LangSmith Trace。


  ----------------------------------------

  # Prompt管理


  所有Prompt独立文件。


  禁止写Python字符串。


  目录：


  prompts/


  planner.md

  metric.md

  log.md

  tool.md

  reflection.md

  report.md

  

  ----------------------------------------

  # 配置管理


  统一：


  .env


  config/


  settings.py

  

  支持：

  dev

  test

  prod

  

  ----------------------------------------

  # API设计


  提供：


  POST /chat


  POST /incident


  GET /history


  GET /tools


  POST /rag/upload


  POST /knowledge/search


  GET /health


  GET /metrics


  POST /agent/replay

  

  ----------------------------------------

  # SSE流式输出


  支持实时返回Agent执行过程。


  例如：


  Planning...


  Query Metrics...


  Searching Logs...


  Searching Knowledge...


  Analyzing...


  Waiting Approval...


  Executing...


  Generating Report...

  

  ----------------------------------------

  # 数据库设计


  MySQL。


  设计完整Schema：


  users


  sessions


  conversation


  message


  incident


  agent_trace


  tool_call


  tool_result


  documents


  knowledge


  chunk


  report


  experience


  workflow


  approval

  

  ----------------------------------------

  # Redis用途


  Redis用于：


  Session缓存


  Conversation缓存


  Agent状态


  Workflow Checkpoint


  分布式锁

  

  ----------------------------------------

  # Milvus用途


  只保存向量数据。


  包括：


  Knowledge Chunk


  Embedding Vector


  Metadata

  

  业务数据禁止存Milvus。

  

  ----------------------------------------

  # 日志


  统一：

  Loguru


  记录：


  API请求

  Agent流程

  Tool调用

  LLM调用

  Token

  异常

  

  ----------------------------------------

  # 测试


  pytest。


  覆盖：


  Tool


  RAG


  Workflow


  Agent


  Memory


  API

  

  ----------------------------------------

  # Docker


  提供：


  docker-compose.yml


  包含：


  FastAPI


  MySQL


  Redis


  Milvus

  

  ----------------------------------------

  # 项目目录


  要求：


  app/


      api/


      agents/


      workflows/


      tools/


          metric/


          log/


          executor/


          knowledge/


      rag/


      memory/


      models/


      repositories/


      services/


      prompts/


      providers/


      adapters/


      config/


      schemas/


      utils/

  

  ----------------------------------------

  # 开发原则


  遵循：


  SOLID


  DDD(轻量)


  Dependency Injection


  Adapter Pattern


  Factory Pattern


  Strategy Pattern


  Repository Pattern

  

  禁止：

  God Class

  硬编码

  业务耦合


  ----------------------------------------

  # 输出要求


  禁止一次生成完整项目。


  必须按照企业开发流程。


  阶段：


  第一阶段：

  初始化项目

  目录结构

  依赖

  配置


  第二阶段：

  MySQL数据库设计

  SQLAlchemy Model

  Repository


  第三阶段：

  Tool接口设计


  第四阶段：

  Mock Tool实现


  第五阶段：

  Embedding Provider

  RAG系统


  第六阶段：

  Memory系统


  第七阶段：

  LangGraph Multi-Agent


  第八阶段：

  Workflow


  第九阶段：

  API接口


  第十阶段：

  Docker部署


  第十一阶段：

  测试完善

  

  每完成一个阶段：


  必须输出：


  1. 完整代码

  2. 架构说明

  3. 设计原因

  4. 扩展方式

  5. 代码质量检查


  确认无问题后再进入下一阶段。

  

  ----------------------------------------

  # 代码要求


  所有代码：

  - Python类型注解完整
  - Pydantic模型规范
  - Docstring完整
  - Ruff检查通过
  - Black格式
  - isort排序
  - 高内聚低耦合
  - 企业生产级代码质量

  目标：

  作为GitHub开源项目和个人简历项目。