from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

LOTTIE_SYSTEM_PROMPT = """You are a professional Lottie animation generator. You create valid Lottie JSON animations based on user descriptions.

CRITICAL RULES:
1. Return ONLY valid JSON - no markdown, no code blocks, no explanation text
2. The JSON must be a valid Lottie animation format
3. Use smooth easing curves (bezier) for professional motion
4. Keep animations loopable when appropriate
5. Use vibrant colors and smooth transitions
6. Standard canvas: 512x512, 30fps, 60-120 frames

LOTTIE JSON STRUCTURE:
{
  "v": "5.7.4",
  "fr": 30,
  "ip": 0,
  "op": 60,
  "w": 512,
  "h": 512,
  "nm": "animation_name",
  "ddd": 0,
  "assets": [],
  "layers": [...]
}

LAYER TYPES:
- ty: 4 = Shape Layer (most common, use this for shapes)
- ty: 0 = Precomp Layer
- ty: 1 = Solid Layer
- ty: 3 = Null Layer

SHAPE LAYER STRUCTURE (ty: 4):
Each shape layer has "shapes" array containing shape items:
- "ty": "gr" = Group (contains items array with shapes + transforms)
- "ty": "rc" = Rectangle (with "s" for size, "p" for position, "r" for roundness)
- "ty": "el" = Ellipse (with "s" for size, "p" for position)
- "ty": "sr" = Polystar (stars, polygons)
- "ty": "sh" = Path (with "ks" containing vertices "v", in-tangents "i", out-tangents "o", closed "c")
- "ty": "fl" = Fill (with "c" color, "o" opacity)
- "ty": "st" = Stroke (with "c" color, "o" opacity, "w" width)
- "ty": "tr" = Transform (position, scale, rotation, opacity, anchor)
- "ty": "tm" = Trim Paths (for stroke animations)

COLOR FORMAT: {"a": 0, "k": [r, g, b, 1]} where r,g,b are 0-1 floats

TRANSFORM PROPERTIES (in layer "ks"):
- "o": opacity (0-100)
- "r": rotation (degrees)
- "p": position {"a":0,"k":[x,y]}
- "a": anchor point {"a":0,"k":[x,y]}
- "s": scale {"a":0,"k":[100,100]}

KEYFRAME ANIMATION:
To animate a property, set "a": 1 and "k" to array of keyframes:
{
  "a": 1,
  "k": [
    {"t": 0, "s": [start_value], "e": [end_value], "i": {"x":[0.42],"y":[1]}, "o": {"x":[0.58],"y":[0]}},
    {"t": 30, "s": [end_value]}
  ]
}
- "t" = time (frame number)
- "s" = start value at this keyframe
- "e" = end value (interpolate to)
- "i" = bezier in-tangent (ease-in)
- "o" = bezier out-tangent (ease-out)

EASING PRESETS:
- Linear: i:{x:[1],y:[1]}, o:{x:[0],y:[0]}
- Ease-in-out: i:{x:[0.42],y:[1]}, o:{x:[0.58],y:[0]}
- Bounce: i:{x:[0.17],y:[1.52]}, o:{x:[0.83],y:[-0.52]}
- Elastic: multiple keyframes with overshoot

COMMON PATTERNS:
1. Pulsing circle: Ellipse with animated scale (100->120->100)
2. Spinning element: Animated rotation (0->360)
3. Bouncing: Animated position Y with ease
4. Fade in/out: Animated opacity
5. Color change: Animated fill color
6. Path drawing: Trim paths animation (start 0->100%)
7. Morphing: Animated path vertices

For complex animations, use multiple layers with different blend modes and timing offsets.
Always ensure shapes have both fill/stroke AND transform in groups.
Make animations visually appealing with complementary colors and smooth motion.

IMPORTANT: Output ONLY the raw JSON object. No wrapping, no explanation."""

ENHANCE_SYSTEM_PROMPT = """You are a Lottie animation enhancer. You receive existing Lottie JSON and enhancement instructions. 
Modify the animation to incorporate the requested changes while keeping it valid.

RULES:
1. Return ONLY the modified valid Lottie JSON
2. Preserve the overall structure
3. Add/modify layers, shapes, or keyframes as requested
4. Keep animations smooth and professional
5. No markdown, no code blocks, no explanation - ONLY raw JSON"""


class GenerateRequest(BaseModel):
    prompt: str
    api_key: Optional[str] = None
    provider: str = "openai"
    model: str = "gpt-5.2"


class EnhanceRequest(BaseModel):
    lottie_json: dict
    prompt: str
    api_key: Optional[str] = None
    provider: str = "openai"
    model: str = "gpt-5.2"


class SaveAnimationRequest(BaseModel):
    name: str
    prompt: str
    lottie_json: dict


class AnimationRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    prompt: str
    lottie_json: dict
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def get_api_key(user_key: Optional[str] = None) -> str:
    if user_key and user_key.strip():
        return user_key.strip()
    key = os.environ.get('EMERGENT_LLM_KEY', '')
    if not key:
        raise HTTPException(status_code=400, detail="No API key available. Please provide an API key in settings.")
    return key


def clean_json_response(text: str) -> dict:
    """Extract and parse JSON from LLM response, handling markdown code blocks."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        start = 1
        end = len(lines)
        for i, line in enumerate(lines):
            if i > 0 and line.strip().startswith("```"):
                end = i
                break
        cleaned = "\n".join(lines[start:end]).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(cleaned[start:end])
        raise HTTPException(status_code=500, detail="Failed to parse animation JSON from AI response")


@api_router.get("/")
async def root():
    return {"message": "LottieFlow Studio API"}


@api_router.post("/generate")
async def generate_animation(req: GenerateRequest):
    try:
        api_key = get_api_key(req.api_key)
        session_id = str(uuid.uuid4())
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=LOTTIE_SYSTEM_PROMPT
        )
        if req.provider and req.model:
            chat.with_model(req.provider, req.model)
        else:
            chat.with_model("openai", "gpt-5.2")

        user_msg = UserMessage(text=f"Create a Lottie animation: {req.prompt}")
        response = await chat.send_message(user_msg)
        lottie_data = clean_json_response(response)

        if "v" not in lottie_data or "layers" not in lottie_data:
            raise HTTPException(status_code=500, detail="Generated JSON is not a valid Lottie animation")

        return {"success": True, "lottie_json": lottie_data, "prompt": req.prompt}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Animation generation failed: {str(e)}")


@api_router.post("/enhance")
async def enhance_animation(req: EnhanceRequest):
    try:
        api_key = get_api_key(req.api_key)
        session_id = str(uuid.uuid4())
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=ENHANCE_SYSTEM_PROMPT
        )
        if req.provider and req.model:
            chat.with_model(req.provider, req.model)
        else:
            chat.with_model("openai", "gpt-5.2")

        existing_json = json.dumps(req.lottie_json, indent=2)
        user_msg = UserMessage(
            text=f"Here is the existing Lottie animation JSON:\n{existing_json}\n\nPlease enhance it with: {req.prompt}"
        )
        response = await chat.send_message(user_msg)
        lottie_data = clean_json_response(response)

        return {"success": True, "lottie_json": lottie_data, "prompt": req.prompt}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhancement error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Animation enhancement failed: {str(e)}")


@api_router.post("/history")
async def save_animation(req: SaveAnimationRequest):
    record = AnimationRecord(name=req.name, prompt=req.prompt, lottie_json=req.lottie_json)
    doc = record.model_dump()
    await db.animations.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.get("/history")
async def get_history():
    animations = await db.animations.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return animations


@api_router.delete("/history/{animation_id}")
async def delete_animation(animation_id: str):
    result = await db.animations.delete_one({"id": animation_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Animation not found")
    return {"success": True}


@api_router.get("/templates")
async def get_templates():
    return BUILT_IN_TEMPLATES


BUILT_IN_TEMPLATES = [
    {
        "id": "pulse-circle",
        "name": "Pulsing Circle",
        "category": "Basic",
        "description": "A smooth pulsing circle animation",
        "lottie_json": {
            "v": "5.7.4", "fr": 30, "ip": 0, "op": 60, "w": 512, "h": 512, "nm": "Pulse", "ddd": 0, "assets": [],
            "layers": [{
                "ddd": 0, "ind": 0, "ty": 4, "nm": "Circle", "sr": 1, "ks": {
                    "o": {"a": 0, "k": 100}, "r": {"a": 0, "k": 0},
                    "p": {"a": 0, "k": [256, 256, 0]}, "a": {"a": 0, "k": [0, 0, 0]},
                    "s": {"a": 1, "k": [
                        {"t": 0, "s": [100, 100, 100], "e": [120, 120, 100], "i": {"x": [0.42, 0.42, 0.42], "y": [1, 1, 1]}, "o": {"x": [0.58, 0.58, 0.58], "y": [0, 0, 0]}},
                        {"t": 30, "s": [120, 120, 100], "e": [100, 100, 100], "i": {"x": [0.42, 0.42, 0.42], "y": [1, 1, 1]}, "o": {"x": [0.58, 0.58, 0.58], "y": [0, 0, 0]}},
                        {"t": 60, "s": [100, 100, 100]}
                    ]}
                },
                "ao": 0, "shapes": [{
                    "ty": "gr", "it": [
                        {"d": 1, "ty": "el", "s": {"a": 0, "k": [200, 200]}, "p": {"a": 0, "k": [0, 0]}, "nm": "Ellipse"},
                        {"ty": "fl", "c": {"a": 0, "k": [0.231, 0.51, 0.965, 1]}, "o": {"a": 0, "k": 100}, "r": 1, "nm": "Fill"},
                        {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}}
                    ], "nm": "Group", "np": 3
                }],
                "ip": 0, "op": 60, "st": 0
            }]
        }
    },
    {
        "id": "spinning-star",
        "name": "Spinning Star",
        "category": "Basic",
        "description": "A colorful spinning star",
        "lottie_json": {
            "v": "5.7.4", "fr": 30, "ip": 0, "op": 90, "w": 512, "h": 512, "nm": "SpinningStar", "ddd": 0, "assets": [],
            "layers": [{
                "ddd": 0, "ind": 0, "ty": 4, "nm": "Star", "sr": 1, "ks": {
                    "o": {"a": 0, "k": 100},
                    "r": {"a": 1, "k": [
                        {"t": 0, "s": [0], "e": [360], "i": {"x": [0.42], "y": [1]}, "o": {"x": [0.58], "y": [0]}},
                        {"t": 90, "s": [360]}
                    ]},
                    "p": {"a": 0, "k": [256, 256, 0]}, "a": {"a": 0, "k": [0, 0, 0]}, "s": {"a": 0, "k": [100, 100, 100]}
                },
                "ao": 0, "shapes": [{
                    "ty": "gr", "it": [
                        {"ty": "sr", "sy": 1, "d": 1, "pt": {"a": 0, "k": 5}, "p": {"a": 0, "k": [0, 0]}, "r": {"a": 0, "k": 0},
                         "ir": {"a": 0, "k": 50}, "is": {"a": 0, "k": 0}, "or": {"a": 0, "k": 120}, "os": {"a": 0, "k": 0}, "nm": "Star"},
                        {"ty": "fl", "c": {"a": 1, "k": [
                            {"t": 0, "s": [0.961, 0.388, 0.141, 1], "e": [0.925, 0.192, 0.478, 1], "i": {"x": [0.42], "y": [1]}, "o": {"x": [0.58], "y": [0]}},
                            {"t": 45, "s": [0.925, 0.192, 0.478, 1], "e": [0.961, 0.388, 0.141, 1], "i": {"x": [0.42], "y": [1]}, "o": {"x": [0.58], "y": [0]}},
                            {"t": 90, "s": [0.961, 0.388, 0.141, 1]}
                        ]}, "o": {"a": 0, "k": 100}, "r": 1, "nm": "Fill"},
                        {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}}
                    ], "nm": "Group", "np": 3
                }],
                "ip": 0, "op": 90, "st": 0
            }]
        }
    },
    {
        "id": "bouncing-ball",
        "name": "Bouncing Ball",
        "category": "Motion",
        "description": "A realistic bouncing ball with squash and stretch",
        "lottie_json": {
            "v": "5.7.4", "fr": 30, "ip": 0, "op": 60, "w": 512, "h": 512, "nm": "Bounce", "ddd": 0, "assets": [],
            "layers": [
                {
                    "ddd": 0, "ind": 0, "ty": 4, "nm": "Shadow", "sr": 1, "ks": {
                        "o": {"a": 1, "k": [
                            {"t": 0, "s": [30], "e": [80], "i": {"x": [0.42], "y": [1]}, "o": {"x": [0.58], "y": [0]}},
                            {"t": 30, "s": [80], "e": [30], "i": {"x": [0.42], "y": [1]}, "o": {"x": [0.58], "y": [0]}},
                            {"t": 60, "s": [30]}
                        ]},
                        "r": {"a": 0, "k": 0}, "p": {"a": 0, "k": [256, 420, 0]}, "a": {"a": 0, "k": [0, 0, 0]},
                        "s": {"a": 1, "k": [
                            {"t": 0, "s": [60, 20, 100], "e": [100, 20, 100], "i": {"x": [0.42, 0.42, 0.42], "y": [1, 1, 1]}, "o": {"x": [0.58, 0.58, 0.58], "y": [0, 0, 0]}},
                            {"t": 30, "s": [100, 20, 100], "e": [60, 20, 100], "i": {"x": [0.42, 0.42, 0.42], "y": [1, 1, 1]}, "o": {"x": [0.58, 0.58, 0.58], "y": [0, 0, 0]}},
                            {"t": 60, "s": [60, 20, 100]}
                        ]}
                    },
                    "ao": 0, "shapes": [{"ty": "gr", "it": [
                        {"d": 1, "ty": "el", "s": {"a": 0, "k": [150, 30]}, "p": {"a": 0, "k": [0, 0]}, "nm": "Shadow"},
                        {"ty": "fl", "c": {"a": 0, "k": [0.1, 0.1, 0.1, 1]}, "o": {"a": 0, "k": 50}, "r": 1, "nm": "Fill"},
                        {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}}
                    ], "nm": "Group", "np": 3}],
                    "ip": 0, "op": 60, "st": 0
                },
                {
                    "ddd": 0, "ind": 1, "ty": 4, "nm": "Ball", "sr": 1, "ks": {
                        "o": {"a": 0, "k": 100}, "r": {"a": 0, "k": 0},
                        "p": {"a": 1, "k": [
                            {"t": 0, "s": [256, 120, 0], "e": [256, 380, 0], "i": {"x": 0.55, "y": 1}, "o": {"x": 0.45, "y": 0}, "to": [0, 0, 0], "ti": [0, 0, 0]},
                            {"t": 30, "s": [256, 380, 0], "e": [256, 120, 0], "i": {"x": 0.45, "y": 0}, "o": {"x": 0.55, "y": 1}, "to": [0, 0, 0], "ti": [0, 0, 0]},
                            {"t": 60, "s": [256, 120, 0]}
                        ]},
                        "a": {"a": 0, "k": [0, 0, 0]},
                        "s": {"a": 1, "k": [
                            {"t": 25, "s": [100, 100, 100], "e": [120, 80, 100], "i": {"x": [0.42, 0.42, 0.42], "y": [1, 1, 1]}, "o": {"x": [0.58, 0.58, 0.58], "y": [0, 0, 0]}},
                            {"t": 30, "s": [120, 80, 100], "e": [95, 105, 100], "i": {"x": [0.42, 0.42, 0.42], "y": [1, 1, 1]}, "o": {"x": [0.58, 0.58, 0.58], "y": [0, 0, 0]}},
                            {"t": 35, "s": [95, 105, 100], "e": [100, 100, 100], "i": {"x": [0.42, 0.42, 0.42], "y": [1, 1, 1]}, "o": {"x": [0.58, 0.58, 0.58], "y": [0, 0, 0]}},
                            {"t": 40, "s": [100, 100, 100]}
                        ]}
                    },
                    "ao": 0, "shapes": [{"ty": "gr", "it": [
                        {"d": 1, "ty": "el", "s": {"a": 0, "k": [100, 100]}, "p": {"a": 0, "k": [0, 0]}, "nm": "Ball"},
                        {"ty": "fl", "c": {"a": 0, "k": [0.133, 0.827, 0.506, 1]}, "o": {"a": 0, "k": 100}, "r": 1, "nm": "Fill"},
                        {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}}
                    ], "nm": "Group", "np": 3}],
                    "ip": 0, "op": 60, "st": 0
                }
            ]
        }
    },
    {
        "id": "loading-dots",
        "name": "Loading Dots",
        "category": "UI",
        "description": "Animated loading dots for UI",
        "lottie_json": {
            "v": "5.7.4", "fr": 30, "ip": 0, "op": 60, "w": 512, "h": 512, "nm": "LoadingDots", "ddd": 0, "assets": [],
            "layers": [
                {
                    "ddd": 0, "ind": 0, "ty": 4, "nm": "Dot1", "sr": 1, "ks": {
                        "o": {"a": 0, "k": 100}, "r": {"a": 0, "k": 0},
                        "p": {"a": 1, "k": [
                            {"t": 0, "s": [176, 256, 0], "e": [176, 216, 0], "i": {"x": 0.42, "y": 1}, "o": {"x": 0.58, "y": 0}, "to": [0, 0, 0], "ti": [0, 0, 0]},
                            {"t": 10, "s": [176, 216, 0], "e": [176, 256, 0], "i": {"x": 0.42, "y": 1}, "o": {"x": 0.58, "y": 0}, "to": [0, 0, 0], "ti": [0, 0, 0]},
                            {"t": 20, "s": [176, 256, 0]}
                        ]},
                        "a": {"a": 0, "k": [0, 0, 0]}, "s": {"a": 0, "k": [100, 100, 100]}
                    },
                    "ao": 0, "shapes": [{"ty": "gr", "it": [
                        {"d": 1, "ty": "el", "s": {"a": 0, "k": [40, 40]}, "p": {"a": 0, "k": [0, 0]}, "nm": "Dot"},
                        {"ty": "fl", "c": {"a": 0, "k": [0.231, 0.51, 0.965, 1]}, "o": {"a": 0, "k": 100}, "r": 1, "nm": "Fill"},
                        {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}}
                    ], "nm": "Group", "np": 3}],
                    "ip": 0, "op": 60, "st": 0
                },
                {
                    "ddd": 0, "ind": 1, "ty": 4, "nm": "Dot2", "sr": 1, "ks": {
                        "o": {"a": 0, "k": 100}, "r": {"a": 0, "k": 0},
                        "p": {"a": 1, "k": [
                            {"t": 10, "s": [256, 256, 0], "e": [256, 216, 0], "i": {"x": 0.42, "y": 1}, "o": {"x": 0.58, "y": 0}, "to": [0, 0, 0], "ti": [0, 0, 0]},
                            {"t": 20, "s": [256, 216, 0], "e": [256, 256, 0], "i": {"x": 0.42, "y": 1}, "o": {"x": 0.58, "y": 0}, "to": [0, 0, 0], "ti": [0, 0, 0]},
                            {"t": 30, "s": [256, 256, 0]}
                        ]},
                        "a": {"a": 0, "k": [0, 0, 0]}, "s": {"a": 0, "k": [100, 100, 100]}
                    },
                    "ao": 0, "shapes": [{"ty": "gr", "it": [
                        {"d": 1, "ty": "el", "s": {"a": 0, "k": [40, 40]}, "p": {"a": 0, "k": [0, 0]}, "nm": "Dot"},
                        {"ty": "fl", "c": {"a": 0, "k": [0.231, 0.51, 0.965, 1]}, "o": {"a": 0, "k": 100}, "r": 1, "nm": "Fill"},
                        {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}}
                    ], "nm": "Group", "np": 3}],
                    "ip": 0, "op": 60, "st": 0
                },
                {
                    "ddd": 0, "ind": 2, "ty": 4, "nm": "Dot3", "sr": 1, "ks": {
                        "o": {"a": 0, "k": 100}, "r": {"a": 0, "k": 0},
                        "p": {"a": 1, "k": [
                            {"t": 20, "s": [336, 256, 0], "e": [336, 216, 0], "i": {"x": 0.42, "y": 1}, "o": {"x": 0.58, "y": 0}, "to": [0, 0, 0], "ti": [0, 0, 0]},
                            {"t": 30, "s": [336, 216, 0], "e": [336, 256, 0], "i": {"x": 0.42, "y": 1}, "o": {"x": 0.58, "y": 0}, "to": [0, 0, 0], "ti": [0, 0, 0]},
                            {"t": 40, "s": [336, 256, 0]}
                        ]},
                        "a": {"a": 0, "k": [0, 0, 0]}, "s": {"a": 0, "k": [100, 100, 100]}
                    },
                    "ao": 0, "shapes": [{"ty": "gr", "it": [
                        {"d": 1, "ty": "el", "s": {"a": 0, "k": [40, 40]}, "p": {"a": 0, "k": [0, 0]}, "nm": "Dot"},
                        {"ty": "fl", "c": {"a": 0, "k": [0.231, 0.51, 0.965, 1]}, "o": {"a": 0, "k": 100}, "r": 1, "nm": "Fill"},
                        {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}}
                    ], "nm": "Group", "np": 3}],
                    "ip": 0, "op": 60, "st": 0
                }
            ]
        }
    },
    {
        "id": "checkmark",
        "name": "Success Checkmark",
        "category": "UI",
        "description": "Animated success checkmark",
        "lottie_json": {
            "v": "5.7.4", "fr": 30, "ip": 0, "op": 40, "w": 512, "h": 512, "nm": "Check", "ddd": 0, "assets": [],
            "layers": [
                {
                    "ddd": 0, "ind": 0, "ty": 4, "nm": "Circle", "sr": 1, "ks": {
                        "o": {"a": 0, "k": 100}, "r": {"a": 0, "k": 0},
                        "p": {"a": 0, "k": [256, 256, 0]}, "a": {"a": 0, "k": [0, 0, 0]},
                        "s": {"a": 1, "k": [
                            {"t": 0, "s": [0, 0, 100], "e": [100, 100, 100], "i": {"x": [0.17, 0.17, 0.17], "y": [1, 1, 1]}, "o": {"x": [0.83, 0.83, 0.83], "y": [0, 0, 0]}},
                            {"t": 15, "s": [100, 100, 100]}
                        ]}
                    },
                    "ao": 0, "shapes": [{"ty": "gr", "it": [
                        {"d": 1, "ty": "el", "s": {"a": 0, "k": [200, 200]}, "p": {"a": 0, "k": [0, 0]}, "nm": "BG"},
                        {"ty": "fl", "c": {"a": 0, "k": [0.063, 0.725, 0.506, 1]}, "o": {"a": 0, "k": 100}, "r": 1, "nm": "Fill"},
                        {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}}
                    ], "nm": "Group", "np": 3}],
                    "ip": 0, "op": 40, "st": 0
                },
                {
                    "ddd": 0, "ind": 1, "ty": 4, "nm": "Check", "sr": 1, "ks": {
                        "o": {"a": 0, "k": 100}, "r": {"a": 0, "k": 0},
                        "p": {"a": 0, "k": [256, 256, 0]}, "a": {"a": 0, "k": [0, 0, 0]}, "s": {"a": 0, "k": [100, 100, 100]}
                    },
                    "ao": 0, "shapes": [{"ty": "gr", "it": [
                        {"ind": 0, "ty": "sh", "ks": {"a": 0, "k": {
                            "i": [[0, 0], [0, 0], [0, 0]], "o": [[0, 0], [0, 0], [0, 0]],
                            "v": [[-40, 0], [-10, 30], [45, -35]], "c": False
                        }}, "nm": "Path"},
                        {"ty": "st", "c": {"a": 0, "k": [1, 1, 1, 1]}, "o": {"a": 0, "k": 100}, "w": {"a": 0, "k": 14}, "lc": 2, "lj": 2, "nm": "Stroke"},
                        {"ty": "tm", "s": {"a": 0, "k": 0}, "e": {"a": 1, "k": [
                            {"t": 12, "s": [0], "e": [100], "i": {"x": [0.42], "y": [1]}, "o": {"x": [0.58], "y": [0]}},
                            {"t": 30, "s": [100]}
                        ]}, "o": {"a": 0, "k": 0}, "m": 1, "nm": "Trim"},
                        {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}}
                    ], "nm": "Group", "np": 3}],
                    "ip": 0, "op": 40, "st": 0
                }
            ]
        }
    },
    {
        "id": "wave-line",
        "name": "Wave Line",
        "category": "Decorative",
        "description": "An animated wave line effect",
        "lottie_json": {
            "v": "5.7.4", "fr": 30, "ip": 0, "op": 90, "w": 512, "h": 512, "nm": "Wave", "ddd": 0, "assets": [],
            "layers": [{
                "ddd": 0, "ind": 0, "ty": 4, "nm": "Wave", "sr": 1, "ks": {
                    "o": {"a": 0, "k": 100}, "r": {"a": 0, "k": 0},
                    "p": {"a": 0, "k": [256, 256, 0]}, "a": {"a": 0, "k": [0, 0, 0]}, "s": {"a": 0, "k": [100, 100, 100]}
                },
                "ao": 0, "shapes": [{"ty": "gr", "it": [
                    {"ind": 0, "ty": "sh", "ks": {"a": 1, "k": [
                        {"t": 0, "s": [{"i": [[0, 0], [-40, -60], [0, 0], [40, 60], [0, 0]], "o": [[40, 60], [0, 0], [-40, -60], [0, 0], [0, 0]], "v": [[-200, 0], [-100, 0], [0, 0], [100, 0], [200, 0]], "c": False}],
                         "e": [{"i": [[0, 0], [-40, 60], [0, 0], [40, -60], [0, 0]], "o": [[40, -60], [0, 0], [-40, 60], [0, 0], [0, 0]], "v": [[-200, 0], [-100, 0], [0, 0], [100, 0], [200, 0]], "c": False}],
                         "i": {"x": 0.42, "y": 1}, "o": {"x": 0.58, "y": 0}},
                        {"t": 45, "s": [{"i": [[0, 0], [-40, 60], [0, 0], [40, -60], [0, 0]], "o": [[40, -60], [0, 0], [-40, 60], [0, 0], [0, 0]], "v": [[-200, 0], [-100, 0], [0, 0], [100, 0], [200, 0]], "c": False}],
                         "e": [{"i": [[0, 0], [-40, -60], [0, 0], [40, 60], [0, 0]], "o": [[40, 60], [0, 0], [-40, -60], [0, 0], [0, 0]], "v": [[-200, 0], [-100, 0], [0, 0], [100, 0], [200, 0]], "c": False}],
                         "i": {"x": 0.42, "y": 1}, "o": {"x": 0.58, "y": 0}},
                        {"t": 90, "s": [{"i": [[0, 0], [-40, -60], [0, 0], [40, 60], [0, 0]], "o": [[40, 60], [0, 0], [-40, -60], [0, 0], [0, 0]], "v": [[-200, 0], [-100, 0], [0, 0], [100, 0], [200, 0]], "c": False}]}
                    ]}, "nm": "Path"},
                    {"ty": "st", "c": {"a": 0, "k": [0.133, 0.827, 0.878, 1]}, "o": {"a": 0, "k": 100}, "w": {"a": 0, "k": 6}, "lc": 2, "lj": 2, "nm": "Stroke"},
                    {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}}
                ], "nm": "Group", "np": 3}],
                "ip": 0, "op": 90, "st": 0
            }]
        }
    }
]

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
