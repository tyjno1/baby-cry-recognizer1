# -*- coding: utf-8 -*-
"""Global Config"""
import os
from dotenv import load_dotenv

load_dotenv()

# DeepSeek Config
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")

# App Config
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.85"))
MAX_HISTORY = int(os.getenv("MAX_HISTORY", "1000"))

# Audio Config
SAMPLE_RATE = 16000
DURATION = 5
N_MFCC = 9

# Need Categories
NEED_CATEGORIES = {
    "hungry": "饿了",
    "poop": "大便",
    "pee": "小便",
    "sleepy": "困了",
    "bored": "无聊/要陪",
    "gassy": "胃胀气/身体不适"
}

# Behavior Patterns
BEHAVIOR_PATTERNS = {
    "trembling": "细微颤抖",
    "mouth_open": "张嘴",
    "hand_foot_waving": "手舞足蹈",
    "body_stiff": "身体僵硬",
    "face_red": "脸红",
    "rubbing_eyes": "揉眼睛",
    "sucking_fingers": "吮手指",
    "arching_back": "挺腰/弓背",
    "kicking_legs": "蹬腿",
    "crying_escalate": "哭声渐强"
}

# Reference Guide Content
REFERENCE_GUIDE = {
    "hungry": {
        "title": "饿了",
        "behaviors": ["mouth_open", "sucking_fingers", "crying_escalate"],
        "cry_features": "短促、有节奏、重复。开始时较轻柔，逐渐变强。给奶嘴时会暂停吮吸。",
        "solution": "及时喂奶。检查喂奶时间表。"
    },
    "poop": {
        "title": "大便",
        "behaviors": ["face_red", "body_stiff", "kicking_legs"],
        "cry_features": "用力声、哼唧声、哭时脸涨红。",
        "solution": "检查尿布。立即更换。如有需要涂抹护臀膏。"
    },
    "pee": {
        "title": "小便",
        "behaviors": ["trembling", "slight_shiver"],
        "cry_features": "突然尖锐的哭声，持续时间短。换尿布后可能停止。",
        "solution": "检查尿布。湿了就换。"
    },
    "sleepy": {
        "title": "困了",
        "behaviors": ["rubbing_eyes", "trembling", "crying_escalate"],
        "cry_features": "哼哼唧唧、烦躁、间歇性。摇晃时会减缓。",
        "solution": "营造安静环境。轻轻摇晃。包裹襁褓。调暗灯光。"
    },
    "bored": {
        "title": "无聊/要陪",
        "behaviors": ["hand_foot_waving", "arching_back", "crying_escalate"],
        "cry_features": "咕咕声转为哭声。抱起或互动时停止。",
        "solution": "抱起、说话、唱歌或提供玩具。改变环境。"
    },
    "gassy": {
        "title": "胃胀气/身体不适",
        "behaviors": ["body_stiff", "arching_back", "kicking_legs", "face_red"],
        "cry_features": "尖锐刺耳、持续不断、难以安抚。常伴随身体扭动、双腿向腹部蜷缩。",
        "solution": "拍嗝排气。做排气操（自行车运动）。飞机抱。顺时针按摩腹部。如持续哭闹需就医。"
    }
}

# DB Path
DB_PATH = "feedback.db"
