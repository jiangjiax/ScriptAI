from langchain.prompts import ChatPromptTemplate
from langchain.schema import AIMessage, HumanMessage
from langchain.chat_models.base import BaseChatModel
from typing import List, Optional, Any, Dict
from pydantic import Field
import requests
import os
from dotenv import load_dotenv
from game_script import CHARACTERS
from langchain_core.runnables import RunnableSequence
import logging

# 加载环境变量
load_dotenv()

class ChatDeepseek(BaseChatModel):
    api_key: str = Field(..., description="DeepSeek API key")
    model_name: str = Field(default="deepseek-chat")
    temperature: float = Field(default=0.8)
    base_url: str = Field(default="https://api.deepseek.com/v1/chat/completions")
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self.api_key = api_key
        
    @property
    def _llm_type(self) -> str:
        """返回 LLM 类型"""
        return "deepseek"
        
    def _call(self, messages: List[Any], stop: Optional[List[str]] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 转换消息格式
        formatted_messages = []
        for message in messages:
            if isinstance(message, (AIMessage, HumanMessage)):
                formatted_messages.append({
                    "role": "assistant" if isinstance(message, AIMessage) else "user",
                    "content": message.content
                })
            elif isinstance(message, dict):
                formatted_messages.append(message)
        
        data = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": self.temperature
        }
        
        if stop:
            data["stop"] = stop
            
        response = requests.post(self.base_url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()["choices"][0]["message"]["content"]
        
    def _generate(self, messages: List[Any], stop: Optional[List[str]] = None) -> str:
        """同步生成回答"""
        return self._call(messages, stop)
        
    async def _agenerate(self, messages: List[Any], stop: Optional[List[str]] = None) -> str:
        return self._call(messages, stop)

class AICharacter:
    def __init__(self):
        self.llm = ChatDeepseek(api_key=os.getenv("DEEPSEEK_API_KEY"))
        self.character_memories = {name: {"conversations": [], "summary": ""} for name in CHARACTERS}
        self.max_recent_conversations = 5
        
        # 更新角色提示模板
        self.prompt_template = """
你正在扮演一个角色参与《Jesse与TYBG的秘密》剧本游戏。

你扮演的角色是：{name}
身份：{身份}
背景：{背景}

你知道的时间线：
{timeline_str}

你的秘密：
- 物证：{秘密[物证]}
- 心理：{秘密[心理]}
- 破绽：{秘密[破绽]}

你掌握的关键线索：{关键线索}

历史对话摘要：{summary}
最近的对话：
{recent_conversations}

玩家问题：{question}

请以角色身份回答，注意：
1. 保持角色特征，说话要符合身份
2. 不要直接透露自己的秘密
3. 可以适当表现出破绽
4. 回答要自然流畅，避免机械化
5. 对于不知道的信息要表现出合理的困惑

回答："""

    def format_character_info(self, char_info: Dict, name: str) -> Dict:
        """格式化角色信息用于提示"""
        timeline_str = "\n".join(
            f"- {time}: {event}" 
            for time, event in char_info["时间线"].items()
        )
        
        recent_convs = self.character_memories[name]["conversations"]
        recent_conversations = "\n".join(
            f"问：{q}\n答：{a}" for q, a in recent_convs
        )
        
        summary = self.character_memories[name]["summary"]
        
        return {
            "name": name,
            **char_info,
            "timeline_str": timeline_str,
            "recent_conversations": recent_conversations,
            "summary": summary
        }

    async def _generate_summary(self, character: str, new_conversations: list):
        """生成对话摘要"""
        previous_summary = self.character_memories[character]["summary"]
        
        # 格式化新对话
        new_chats = "\n".join([
            f"问：{q}\n答：{a}" for q, a in new_conversations
        ])
        
        # 创建摘要提示
        prompt = self.summary_template.format(
            previous_summary=previous_summary,
            new_conversations=new_chats
        )
        
        try:
            messages = [{"role": "user", "content": prompt}]
            summary = await self.llm._agenerate(messages)
            return summary.strip()
        except Exception as e:
            logging.error(f"生成摘要错误: {str(e)}")
            return previous_summary

    async def get_response(self, character: str, question: str) -> str:
        """获取AI角色的回答"""
        if character not in CHARACTERS:
            return "未找到该角色。"
            
        char_info = self.format_character_info(CHARACTERS[character], character)
        char_info["question"] = question
        
        try:
            # 获取回答
            prompt = self.prompt_template.format(**char_info)
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm._agenerate(messages)
            response = response.strip()
            
            # 更新对话历史
            char_memory = self.character_memories[character]
            char_memory["conversations"].append((question, response))
            
            # 如果累积了足够多的新对话，生成摘要
            if len(char_memory["conversations"]) >= self.max_recent_conversations:
                new_summary = await self._generate_summary(
                    character, 
                    char_memory["conversations"]
                )
                char_memory["summary"] = new_summary
                char_memory["conversations"] = []  # 清空最近对话
            
            return response
        except Exception as e:
            logging.error(f"AI响应错误：{str(e)}")
            return "对不起，我现在有点混乱，请稍后再问。" 