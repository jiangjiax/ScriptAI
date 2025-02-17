from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import game_router

app = FastAPI(title="meme_game")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加路由
app.include_router(game_router, prefix="/api/game", tags=["game"]) 