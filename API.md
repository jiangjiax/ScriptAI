# 游戏 API 文档

## 基础信息
- 基础URL: `https://petite-moose-check.loca.lt/api/game`
- 所有POST请求的Content-Type: `application/json`
- 流式响应的Accept: `text/event-stream`

## 接口列表

### 1. 开始新游戏
    POST /start
    
**响应示例:**
    {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "story_background": "游戏背景故事...",
        "available_characters": [
            {
                "name": "Crypto Hunter",
                "title": "数字资产追踪侦探"
            },
            // ...其他角色
        ]
    }

### 2. 所有角色自我介绍
    POST /introduce
    
**请求参数:**
    {
        "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }

**响应示例:**
    {
        "Crypto Hunter": "我是一名数字资产追踪侦探...",
        "Brett": "我是Base生态中最著名的迷因形象...",
        "Art Collector": "作为一名迷因艺术品收藏家..."
    }

### 3. 询问角色
    POST /ask
    
**请求参数:**
    {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "character": "Crypto Hunter",
        "question": "你为什么要监控Brett的交易？"
    }

**响应格式:** Server-Sent Events (SSE)
每个事件的数据格式:
    {
        "start": true/false,    // 开始标记
        "char": "单个字符",     // 逐字返回的内容
        "done": true/false,     // 结束标记
        "error": "错误信息"     // 可选，出错时返回
    }

**SSE 响应示例:**
    data: {"start": true}
    
    data: {"char": "作"}
    data: {"char": "为"}
    data: {"char": "一"}
    data: {"char": "名"}
    ...
    
    data: {"done": true}

**错误响应示例:**
    data: {"error": "AI 响应超时"}

### 4. 指认凶手
    POST /accuse
    
**请求参数:**
    {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "suspect": "Crypto Hunter"
    }

**响应示例 (正确):**
    {
        "correct": true,
        "message": "恭喜你找到了真凶！",
        "case_truth": {
            "凶手": "Crypto Hunter",
            "手法": "...",
            "破案关键点": [...]
        }
    }

**响应示例 (错误):**
    {
        "correct": false,
        "message": "推理错误。真凶是 Crypto Hunter！",
        "case_truth": {...},
        "explanation": "真相揭晓：..."
    }

### 5. 手动结束游戏
    POST /end
    
**请求参数:**
    {
        "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }

**响应示例:**
    {
        "message": "游戏已结束"
    }

### 6. 获取游戏状态
    GET /state?session_id=550e8400-e29b-41d4-a716-446655440000

**请求参数:**
    session_id: 游戏会话ID (必需)

**响应示例:**
    {
        "conversation_history": {
            "Crypto Hunter": {
                "conversations": [...],  // 最近的对话
                "summary": "..."        // 历史对话摘要
            }
        }
    }

## 错误响应
所有接口在发生错误时会返回以下格式：
    {
        "detail": "错误信息描述"
    }

常见错误码：
- 404: 游戏会话不存在/已过期
- 503: 服务器会话数量已达上限
- 500: 服务器内部错误

## 注意事项
1. 游戏会话有效期为2小时，超时后需要重新开始游戏
2. 每个服务器最多支持1000个并发会话
3. 猜测凶手后（无论对错）或手动结束游戏后，会话将被清理
4. 对话历史会自动进行摘要，保留关键信息
5. 流式响应接口需要正确处理SSE数据格式 