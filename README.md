# 📄 PDF-Translate Skill

> **High-Fidelity Vector PDF Translation, Layout Reconstruction & Automated Audit Engine for AI Agents.**  
> 基于大语言模型直译、矢量排版重构、浏览器溢出探针与自动化双向对比自愈的高保真 PDF 翻译技能。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Vector%20PDF-green.svg)](https://playwright.dev/)
[![PyMuPDF](https://img.shields.io/badge/PyMuPDF-Audit%20Engine-orange.svg)](https://pymupdf.readthedocs.io/)

---

## 🌟 核心痛点与解决方案 (Why PDF-Translate?)

传统的文档翻译工具（如通用机翻、常规 OCR 导出）在面对**工程标书、跨国商务合同、法定资质证书、学术白皮书**等严肃公文时，常常面临四大致命难题：

1. **版面坍塌**：表格错位、签章栏截断、页码漂移、目录点线混乱。
2. **位图失真**：将文字光栅化为低分辨率图片，导致无法检索复制、模糊不清。
3. **AI 幻觉脑补**：长文本模型擅自“归纳升华”、擅增/缩减子条款编号或脑补不存在的数字。
4. **跨页溢出**：翻译后的中英文文本长度差异撑爆页面物理高度，导致打印机额外产生空页或乱页。

**`pdf-translate`** 专为解决上述痛点而生，结合大模型精准语义提取与前端 CSS 矢量打印控制，确保翻译结果达到**正式出版与官方公文交付级标准**。

---

## 🚀 核心特性 (Key Features)

- 🎯 **1:1 原版排版还原 (1:1 Layout Preservation)**
  - 严格保持页面尺寸（标准 A4、Letter 等）、物理边距与布局比例。
  - 精准重建双语对照表格、官方公文双栏表头、目录点线对齐（Dotted Leaders）及签字盖章框。
- 🚫 **零幻觉与两阶段解耦规范 (Zero Hallucination Pipeline)**
  - **阶段 1（结构化契约）**：按页先提取条款树、数值、参数与表格结构。
  - **阶段 2（模板化填装）**：严禁压缩、省略或凭常识脑补条款（如法定资质清单 2.1.1~2.1.8）。
- 📐 **浏览器物理高度溢出探针 (JS Height Overflow Probe)**
  - 在无头渲染阶段注入 JavaScript 探针，实时检测每个 `.page` 容器的 `scrollHeight` 与 `clientHeight`。
  - 自动拦截并报警任何可能导致分页错乱的微小溢出。
- 🖨️ **纯矢量无损 PDF 重构 (Publication-Grade Vector PDF)**
  - 基于 Chromium / Edge 内核，输出全矢量、可选中、可搜索、超高清的工业级 PDF。
- 🔍 **自动化对比审计引擎 (`scripts/audit_pdf.py`)**
  - **页数匹配校验**：源文件与目标文件总页数严格 1:1。
  - **纯矢量层校验**：杜绝整页截图/位图伪装。
  - **条款编号逐页双向 Diff**：自动比对章节编号与子条款差集。
  - **敏感词与占位符扫描**：自动拦截 “待补充”、“因篇幅省略”、“详见英文原版” 等 AI 偷懒占位符。

---

## 🏗️ 架构与工作流 (Architecture & Workflow)

```mermaid
flowchart TD
    A[原始 PDF 文档] --> B[步骤 1: PyMuPDF 结构探测与分块规划]
    B --> C[步骤 2: 两阶段数据契约抽取与严谨直译]
    C --> D[步骤 3: 现代化 HTML5 + CSS @page 矢量重构]
    D --> E[步骤 4: Playwright 无头渲染 + JS 溢出探针 (render_pdf.py)]
    E --> F[生成目标矢量 PDF]
    F --> G[步骤 5: audit_pdf.py 自动化审计对比]
    G -->|未通过: 发现溢出/遗漏/编号不符| D
    G -->|通过: 1:1 完美匹配 & 0 报错| H[正式交付发布]
```

---

## 📂 项目结构 (Repository Structure)

```text
pdf-translate/
├── SKILL.md                 # Antigravity / AI Agent 核心技能指令与约束规范
├── requirements.txt         # 核心 Python 依赖项
├── LICENSE                  # MIT 开源协议
├── README.md                # 项目详细说明文档
└── scripts/
    ├── audit_pdf.py         # 1:1 页对页结构、条款双向 Diff 与敏感词自动化审计引擎
    └── render_pdf.py        # 基于 Playwright 的高保真矢量 PDF 渲染脚本 (内置 JS 溢出探针)
```

---

## 🛠️ 安装与快速上手 (Installation & Quick Start)

### 1. 安装依赖

```bash
git clone https://github.com/lxsssssss/pdf-translate.git
cd pdf-translate

pip install -r requirements.txt
playwright install chromium
```

> *注：Windows 环境下亦支持直接调用系统自带的 `msedge` 浏览器信道。*

---

### 2. 命令行工具使用指南

#### 🔹 矢量 PDF 渲染 (`render_pdf.py`)

将排版好的 HTML 源码渲染为物理隔离的矢量 PDF：

```bash
# 基础渲染
python scripts/render_pdf.py input.html output.pdf

# 开启严格模式 (若检测到任何页面高度溢出则立即抛出异常阻断)
python scripts/render_pdf.py input.html output.pdf --strict-overflow
```

#### 🔹 自动化 1:1 对比审计 (`audit_pdf.py`)

比对原版 PDF 与翻译后 PDF 的页码、矢量层、条款编号与文本完整性：

```bash
# 基础对比审计
python scripts/audit_pdf.py --src original.pdf --tgt translated.pdf

# 严格模式 (任何警告均触发非零返回码)
python scripts/audit_pdf.py --src original.pdf --tgt translated.pdf --strict

# 输出结构化 JSON 审计报告 (便于 CI/CD 或 Agent 自动化解析)
python scripts/audit_pdf.py --src original.pdf --tgt translated.pdf --json-out audit_report.json
```

---

## 🤖 在 AI Agent (Antigravity / Claude / Cursor) 中集成

### Google Antigravity
直接将本项目拷贝至工作区的 `.agent/skills/pdf-translate` 目录下：
```text
your-project/
└── .agent/
    └── skills/
        └── pdf-translate/
            ├── SKILL.md
            └── scripts/
```
当你在会话中提出类似 **“帮我把这份招标文件翻译为中文，必须保持原排版并输出为 PDF”** 时，Agent 将自动激活该 Skill 并遵循 SOP 闭环执行。

---

## 📄 开源许可证 (License)

本项目采用 [MIT 许可证](LICENSE)。
