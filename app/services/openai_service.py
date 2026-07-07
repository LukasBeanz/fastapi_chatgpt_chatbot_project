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
from typing import List, Optional

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

# temperature를 지원하지 않는 모델 접두사 목록입니다.
# OpenAI o계열(추론 모델)과 gpt-5 계열은 temperature 파라미터를 받으면 오류가 발생합니다.
_NO_TEMPERATURE_PREFIXES = ("o1", "o2", "o3", "o4", "o5", "gpt-5")


def _supports_temperature(model_name: str) -> bool:
    """모델이 temperature 파라미터를 지원하는지 반환합니다."""
    lower = model_name.lower()
    return not any(lower.startswith(prefix) for prefix in _NO_TEMPERATURE_PREFIXES)

# OpenAI API 키를 환경 변수에서 읽습니다.
# 이 값이 없으면 실제 API 호출 대신 데모 응답을 반환합니다.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# API 키가 있을 때만 OpenAI 클라이언트를 생성합니다.
# 키가 없는데 클라이언트를 무조건 만들면 실행 환경에 따라 오류가 발생할 수 있습니다.
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# 사용자 질문과 이전 대화 내역, 설정 파라미터를 받아 챗봇 답변을 생성하는 함수입니다.
def generate_chat_reply(
    message: str,
    history: List[ChatMessage],
    system_instruction: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
) -> tuple[str, bool]:
    # 실제로 사용할 모델명을 결정합니다. 요청에 모델이 없으면 환경 변수 기본값을 씁니다.
    resolved_model = model or OPENAI_MODEL

    # API 키가 없으면 실제 ChatGPT API를 호출할 수 없습니다.
    # 수업 또는 화면 테스트가 가능하도록 데모 응답을 반환합니다.
    if client is None:
        demo_reply = (
            "현재 OPENAI_API_KEY가 설정되어 있지 않아 데모 모드로 응답합니다. "
            "실제 ChatGPT 답변을 받으려면 프로젝트 루트의 .env 파일에 "
            "OPENAI_API_KEY 값을 설정하세요.\n\n"
            f"입력한 질문: {message}"
        )
        return demo_reply, True

    # system_instruction이 없으면 기본 지시문을 사용합니다.
    effective_system = system_instruction or "너는 한국어로 친절하고 정확하게 답변하는 FastAPI 기반 ChatGPT 챗봇이다."

    # OpenAI API에 전달할 메시지 목록을 생성합니다.
    messages = [{"role": "system", "content": effective_system}]

    # 클라이언트에서 전달한 이전 대화 내역을 OpenAI API 형식으로 변환합니다.
    for item in history:
        if item.role in {"user", "assistant", "system"}:
            messages.append({"role": item.role, "content": item.content})

    # 사용자가 방금 입력한 새 질문을 메시지 목록의 마지막에 추가합니다.
    messages.append({"role": "user", "content": message})

    # API 호출에 사용할 키워드 인자를 동적으로 구성합니다.
    kwargs: dict = {"model": resolved_model, "messages": messages}

    # o계열(o1/o2/o3/o4)과 gpt-5 모델은 temperature를 지원하지 않습니다.
    # 지원 여부를 확인하여 파라미터를 선택적으로 추가합니다.
    if _supports_temperature(resolved_model):
        if temperature is not None:
            kwargs["temperature"] = temperature
        else:
            kwargs["temperature"] = 0.7  # 기본값
        if top_p is not None:
            kwargs["top_p"] = top_p

    # 최대 출력 토큰 수를 설정합니다.
    # o계열 모델은 max_completion_tokens, 그 외는 max_tokens 파라미터명을 사용합니다.
    if max_output_tokens is not None:
        if _supports_temperature(resolved_model):
            kwargs["max_tokens"] = max_output_tokens
        else:
            kwargs["max_completion_tokens"] = max_output_tokens

    # OpenAI Chat Completions API를 호출합니다.
    completion = client.chat.completions.create(**kwargs)

    # 응답 객체에서 첫 번째 답변 메시지 내용을 꺼냅니다.
    reply = completion.choices[0].message.content or "응답 내용이 비어 있습니다."

    # 두 번째 값 False는 실제 API를 사용했다는 의미입니다.
    return reply, False
