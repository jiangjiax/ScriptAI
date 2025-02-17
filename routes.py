from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Optional
from pydantic import BaseModel, Field
from game_logic import GameLogic
import json
import asyncio

game_router = APIRouter()
game_logic = GameLogic()

class QuestionRequest(BaseModel):
    character: str
    question: str

class SearchRequest(BaseModel):
    location: str

class AskRequest(BaseModel):
    session_id: str = Field(..., description="游戏会话ID")
    character: str = Field(..., description="要询问的角色名称")
    question: str = Field(..., description="问题内容", min_length=1, max_length=200)

class AccuseRequest(BaseModel):
    session_id: str = Field(..., description="游戏会话ID")
    suspect: str = Field(..., description="指认的嫌疑人")

class EndGameRequest(BaseModel):
    session_id: str = Field(..., description="游戏会话ID")

class IntroduceRequest(BaseModel):
    session_id: str = Field(..., description="游戏会话ID")

async def stream_character_response(response: str):
    """将角色回答转换为流式响应"""
    try:
        # 发送开始标记
        yield f"data: {json.dumps({'start': True})}\n\n"
        
        # 逐字发送
        for char in response:
            yield f"data: {json.dumps({'char': char})}\n\n"
            await asyncio.sleep(0.05)  # 打字机效果的延迟
            
        # 发送结束标记
        yield f"data: {json.dumps({'done': True})}\n\n"
    except Exception as e:
        # 发送错误信息
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@game_router.post("/start")
async def start_game():
    """开始新游戏"""
    return await game_logic.start_new_game()

@game_router.post("/introduce")
async def all_characters_introduce(request: IntroduceRequest):
    """所有人介绍自己"""
    return await game_logic.get_all_introductions(request.session_id)

@game_router.post("/ask")
async def ask_character(request: AskRequest):
    """询问角色"""
    if not request.question.strip():
        raise HTTPException(status_code=422, detail="问题不能为空")
        
    response = await game_logic.ask_character(
        request.session_id,
        request.character,
        request.question
    )
    
    # 创建 SSE 响应
    stream_response = StreamingResponse(
        stream_character_response(response),
        media_type="text/event-stream"
    )
    
    # 添加必要的 SSE headers
    stream_response.headers["Cache-Control"] = "no-cache"
    stream_response.headers["Connection"] = "keep-alive"
    stream_response.headers["Content-Type"] = "text/event-stream"
    
    return stream_response

@game_router.post("/search")
async def search_location(request: SearchRequest):
    """搜查地点"""
    search_result = await game_logic.search_location(request.location)
    return search_result

@game_router.post("/accuse")
async def accuse_suspect(request: AccuseRequest):
    """指认凶手"""
    return await game_logic.check_murderer(request.session_id, request.suspect)

@game_router.post("/end")
async def end_game(request: EndGameRequest):
    """结束游戏"""
    return await game_logic.end_game(request.session_id)

@game_router.get("/state")
async def get_game_state(session_id: str):
    """获取游戏状态
    
    Args:
        session_id (str): 游戏会话ID，通过查询参数传入
    """
    return await game_logic.get_current_state(session_id) 