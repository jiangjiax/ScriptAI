from fastapi import HTTPException
from game_script import CHARACTERS, CASE_TRUTH, CHARACTER_INTROS
from ai_characters import AICharacter
import uuid
from datetime import datetime, timedelta
import asyncio
import logging

class GameSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.ai = AICharacter()
        self.created_at = datetime.now()
        self.last_active = datetime.now()

class GameLogic:
    def __init__(self):
        self.sessions = {}  # 存储所有游戏会话
        self.session_timeout = timedelta(hours=2)  # 会话超时时间
        self.max_sessions = 1000  # 最大会话数量
        self.cleanup_interval = timedelta(minutes=30)  # 清理间隔
        asyncio.create_task(self._periodic_cleanup())
        
    async def _periodic_cleanup(self):
        """定期清理过期会话"""
        while True:
            try:
                self._cleanup_expired_sessions()
                await asyncio.sleep(self.cleanup_interval.total_seconds())
            except Exception as e:
                logging.error(f"清理会话时出错: {e}")
                
    def _cleanup_expired_sessions(self):
        """清理过期的会话"""
        current_time = datetime.now()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if current_time - session.last_active > self.session_timeout
        ]
        for session_id in expired_sessions:
            del self.sessions[session_id]
            logging.info(f"清理过期会话: {session_id}")
            
    def _get_session(self, session_id: str):
        """获取会话，如果不存在或过期则抛出异常"""
        if session_id not in self.sessions:
            raise HTTPException(status_code=404, detail="游戏会话不存在/已过期")
        
        session = self.sessions[session_id]
        current_time = datetime.now()
        
        if current_time - session.last_active > self.session_timeout:
            del self.sessions[session_id]
            raise HTTPException(status_code=404, detail="游戏会话已过期")
            
        session.last_active = current_time
        return session
        
    async def start_new_game(self):
        """初始化新游戏"""
        if len(self.sessions) >= self.max_sessions:
            raise HTTPException(
                status_code=503, 
                detail="服务器会话数量已达上限，请稍后再试"
            )
            
        self._cleanup_expired_sessions()
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = GameSession(session_id)
        logging.info(f"创建新会话: {session_id}")
        
        return {
            "session_id": session_id,
            "story_background": """
=== 《Jesse与TYBG的秘密》 ===
时间：2024年3月，TYBG社区动荡时期
地点：Base链上的虚拟社区空间

一场突如其来的危机，
TYBG社区内部出现泄密事件，
迷因币价格异常波动，
社区信任正在崩塌。
每个相关者都可能与这场阴谋有关...""",
            "available_characters": [
                {"name": name, "title": info["身份"]}
                for name, info in CHARACTERS.items()
            ]
        }
        
    async def get_all_introductions(self, session_id: str):
        """获取所有角色的自我介绍"""
        session = self._get_session(session_id)
        # 直接返回预设的介绍
        return CHARACTER_INTROS
        
    async def ask_character(self, session_id: str, character: str, question: str):
        """询问角色"""
        session = self._get_session(session_id)
        if character not in CHARACTERS:
            raise HTTPException(status_code=404, detail="未找到该角色")
        
        try:
            # 添加超时处理
            response = await asyncio.wait_for(
                session.ai.get_response(character, question),
                timeout=30.0  # 30秒超时
            )
            return response
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="AI响应超时")
        except Exception as e:
            logging.error(f"AI响应错误: {str(e)}")
            raise HTTPException(status_code=500, detail="AI响应错误")
        
    async def check_murderer(self, session_id: str, suspect: str):
        """验证凶手"""
        session = self._get_session(session_id)
        if suspect not in CHARACTERS:
            raise HTTPException(status_code=404, detail="未找到该角色")
            
        is_correct = suspect == CASE_TRUTH["凶手"]
        
        # 无论对错都删除会话
        del self.sessions[session_id]
        logging.info(f"结束会话(猜测{'正确' if is_correct else '错误'}): {session_id}")
        
        if is_correct:
            return {
                "correct": True,
                "message": "恭喜你找到了真凶！",
                "case_truth": CASE_TRUTH
            }
        else:
            return {
                "correct": False,
                "message": f"推理错误。真凶是 {CASE_TRUTH['凶手']}！",
                "case_truth": CASE_TRUTH,
                "explanation": f"""
真相揭晓：
{CASE_TRUTH['手法']}

关键线索：
- {CASE_TRUTH['破案关键点'][0]}
- {CASE_TRUTH['破案关键点'][1]}
- {CASE_TRUTH['破案关键点'][2]}
"""
            }
        
    async def get_current_state(self, session_id: str):
        """获取当前游戏状态"""
        session = self._get_session(session_id)
        return {
            "conversation_history": session.ai.character_memories
        }

    async def end_game(self, session_id: str):
        """手动结束游戏"""
        session = self._get_session(session_id)
        del self.sessions[session_id]
        logging.info(f"手动结束会话: {session_id}")
        return {"message": "游戏已结束"} 