# app/services/openai_service.py
# ------------------------------------------------------------
# 이 파일은 OpenAI API 호출 로직을 담당합니다.
# 라우터(main.py)에 모든 코드를 몰아넣지 않고 서비스 파일로 분리하면 유지보수가 쉬워집니다.
# ------------------------------------------------------------

# os 모듈은 환경 변수 값을 읽을 때 사용합니다.
# API 키는 코드에 직접 작성하면 유출 위험이 있으므로 환경 변수로 관리합니다.
import os

# typing 모듈에서 List 타입을 가져옵니다.
# 대화 기록 목록의 타입을 명확히 표현하기 위해 사용합니다.
from typing import List

# dotenv의 load_dotenv 함수를 가져옵니다.
# .env 파일에 저장된 OPENAI_API_KEY 값을 파이썬 환경 변수로 불러오기 위해 사용합니다.
from dotenv import load_dotenv

# OpenAI 공식 파이썬 SDK의 OpenAI 클래스를 가져옵니다.
# 이 클래스를 통해 Chat Completions API를 호출합니다.
from openai import OpenAI

# 앞에서 정의한 ChatMessage 모델을 가져옵니다.
# 요청으로 전달된 대화 기록을 타입 힌트로 사용합니다.
from app.schemas import ChatMessage

# 프로젝트 루트에 있는 .env 파일을 읽습니다.
# .env 파일이 없어도 오류를 발생시키지 않으므로 개발과 배포 환경 모두에서 사용할 수 있습니다.
load_dotenv()

# 기본 모델명을 환경 변수에서 읽습니다.
# 환경 변수 OPENAI_MODEL이 없으면 gpt-4o-mini를 기본값으로 사용합니다.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# OpenAI API 키를 환경 변수에서 읽습니다.
# 이 값이 없으면 실제 API 호출 대신 데모 응답을 반환합니다.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# API 키가 있을 때만 OpenAI 클라이언트를 생성합니다.
# 키가 없는데 클라이언트를 무조건 만들면 실행 환경에 따라 오류가 발생할 수 있습니다.
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# 사용자 질문과 이전 대화 내역을 받아 챗봇 답변을 생성하는 함수입니다.
def generate_chat_reply(message: str, history: List[ChatMessage]) -> tuple[str, bool]:
    # API 키가 없으면 실제 ChatGPT API를 호출할 수 없습니다.
    # 수업 또는 화면 테스트가 가능하도록 데모 응답을 반환합니다.
    if client is None:
        # 데모 모드 안내 문장을 생성합니다.
        demo_reply = (
            "현재 OPENAI_API_KEY가 설정되어 있지 않아 데모 모드로 응답합니다. "
            "실제 ChatGPT 답변을 받으려면 프로젝트 루트의 .env 파일에 "
            "OPENAI_API_KEY 값을 설정하세요.\n\n"
            f"입력한 질문: {message}"
        )

        # 두 번째 값 True는 데모 모드를 사용했다는 의미입니다.
        return demo_reply, True

    # OpenAI API에 전달할 메시지 목록을 생성합니다.
    # 첫 번째 system 메시지는 챗봇의 역할과 답변 스타일을 지정합니다.
    messages = [
        {
            "role": "system",
            "content": "너는 한국어로 친절하고 정확하게 답변하는 FastAPI 기반 ChatGPT 챗봇이다.",
        }
    ]

    # 클라이언트에서 전달한 이전 대화 내역을 OpenAI API 형식으로 변환합니다.
    for item in history:
        # 허용된 role만 API 메시지에 추가합니다.
        # 잘못된 role이 들어오면 OpenAI API 오류가 발생할 수 있으므로 필터링합니다.
        if item.role in {"user", "assistant", "system"}:
            # Pydantic 모델의 값을 딕셔너리로 변환하여 messages에 추가합니다.
            messages.append({"role": item.role, "content": item.content})

    # 사용자가 방금 입력한 새 질문을 메시지 목록의 마지막에 추가합니다.
    messages.append({"role": "user", "content": message})

    # OpenAI Chat Completions API를 호출합니다.
    # temperature는 답변의 창의성 정도이며, 0에 가까울수록 일관적이고 1에 가까울수록 다양해집니다.
    completion = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.7,
    )

    # 응답 객체에서 첫 번째 답변 메시지 내용을 꺼냅니다.
    reply = completion.choices[0].message.content or "응답 내용이 비어 있습니다."

    # 두 번째 값 False는 실제 API를 사용했다는 의미입니다.
    return reply, False
