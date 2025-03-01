# AI Murder Mystery - DeepSeek 剧本杀 Demo

基于 DeepSeek 大模型的智能剧本杀演示系统，实现AI主持人与玩家的沉浸式互动推理体验。

## 核心功能

- 🕵️ **AI角色扮演** - 每个NPC拥有独立记忆和角色设定
- 🎭 **多阶段游戏流程** - 包含案情陈述、调查阶段、集中讨论、投票判决
- 🧠 **实时推理系统** - 基于DeepSeek的智能问答与线索生成
- ⚖️ **自动裁判系统** - 支持指控验证与反馈机制
- 📊 **游戏状态监控** - 实时可视化查看各角色交互数据

## 技术栈

| 模块        | 技术选型                             |
|-----------|----------------------------------|
| **AI 核心**  | DeepSeek API / LangChain         |
| **后端**     | Python + FastAPI                 |
