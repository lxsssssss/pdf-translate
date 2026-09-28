# 项目状态与跨会话备忘录 (Project Handover Memo)

- **主项目**: [pdf-translate](https://github.com/lxsssssss/pdf-translate) (已发布 v1.0.0 Release，⭐ **101 Stars**，突破百星里程碑！)
- **本地路径**: `E:\antigravity_workspace\pdf-translate`
- **关联上一个长会话**: [查看前置会话记录](conversation://8dd4f406-83ea-412d-bbbe-f93959f7bbe7) (ID: `8dd4f406-83ea-412d-bbbe-f93959f7bbe7`)

---

## 1. 三大顶流 Awesome 榜单收录状态 (最新跟踪)

1. **`Shubhamsaboo/awesome-llm-apps` (25k+ Stars)**
   - **原 PR**: [#1180](https://github.com/Shubhamsaboo/awesome-llm-apps/pull/1180)
   - **状态**: ⚠️ `Closed`（上游维护者 Shubham Saboo 于 9-21 合并 PR #1195 进行架构大改，统一推行 `agent_skills/` 规范与 `agentskills.io` 注册表，并批量清理关闭了一批旧路径提交）。可按其最新 `agent_skills/` 标准重新发起提交。
   - **本地分支**: `E:\antigravity_workspace\awesome-llm-apps` (`feature/layout-preserving-pdf-translator`)

2. **`e2b-dev/awesome-ai-agents` (17k+ Stars)**
   - **PR**: [#1575](https://github.com/e2b-dev/awesome-ai-agents/pull/1575)
   - **状态**: ✅ `Open` | `Mergeable: True` | `State: Clean`。CLA 已签，CI 自动化检查全部通过，持续排队等待官方批量合并。

3. **`PatrickJS/awesome-cursorrules` (23k+ Stars)**
   - **PR**: [#378](https://github.com/PatrickJS/awesome-cursorrules/pull/378)
   - **状态**: ✅ `Open` | `Mergeable: True`。5 项核心 CI 检查全绿通过，CodeRabbit 细节建议已全解决，排队等待维护者合并。

---

## 2. 项目核心演进与成果归档 (v2.3.0)

- **README 演示图安全合规 (方案 B) - 全部完成并上线**:
  - 使用深度学习里程碑论文《Attention Is All You Need》（arXiv:1706.03762）前 10 页作为公版基准案例，彻底规避商业或敏感信息。
  - **完成第 1 页与第 3 页 1:1 像素级精修并上传**:
    - `assets/comparison_cover.png`: 论文封面（4pt/1pt 双线标题框、8位作者矩阵、arXiv竖排条、单栏摘要、143.5pt 短横脚注线）。
    - `assets/comparison_page_03.png`: Transformer 整体架构图（218.9pt x 322.4pt 原图真实比例与正文垂直基线精准锚定）。
  - **自动化质检全项通过**: 10/10 PASS，0 严重错误，0 警告。

- **Skill 升级至 v2.3.0**:
  - 确立“几何探针优先（Geometry Probe First）”原则，杜绝无脑 `max-height` 压缩；
  - 增加几何线条高保真复刻（`get_drawings()`）；
  - 引入中文信息密度补偿与垂直基线对齐策略；
  - 建立生成后自动化审计与用户视觉审阅确认双重门禁。
