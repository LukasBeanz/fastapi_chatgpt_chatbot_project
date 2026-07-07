# app/schemas.py
# ------------------------------------------------------------
# 이 파일은 FastAPI 요청(Request)과 응답(Response)의 데이터 형식을 정의합니다.
# Pydantic 모델을 사용하면 잘못된 데이터가 들어왔을 때 FastAPI가 자동으로 검증합니다.
# ------------------------------------------------------------

# typing 모듈에서 List 타입을 가져옵니다.
# List는 여러 개의 데이터를 담는 리스트 자료형의 내부 타입을 명확히 표현할 때 사용합니다.
from typing import List, Optional

# pydantic의 BaseModel과 Field를 가져옵니다.
# BaseModel은 데이터 검증 모델의 기본 클래스입니다.
# Field는 각 필드의 설명, 기본값, 길이 제한 등을 지정할 때 사용합니다.
from pydantic import BaseModel, Field


# 채팅 메시지 1개의 구조를 정의하는 클래스입니다.
# 사용자의 메시지와 챗봇의 메시지를 같은 형식으로 다루기 위해 사용합니다.
class ChatMessage(BaseModel):
    # role은 메시지를 보낸 주체를 의미합니다.
    # OpenAI Chat Completions API에서는 일반적으로 system, user, assistant 역할을 사용합니다.
    role: str = Field(
        ...,                                      # ...은 필수 입력값이라는 뜻입니다.
        description="메시지 역할: system, user, assistant 중 하나",
        examples=["user"],
    )

    # content는 실제 메시지 내용입니다.
    # min_length=1을 지정하여 빈 문자열이 들어오지 않도록 검증합니다.
    content: str = Field(
        ...,
        min_length=1,
        description="메시지 본문",
        examples=["FastAPI가 무엇인가요?"],
    )


# 클라이언트가 /api/chat 엔드포인트로 보낼 요청 데이터 구조입니다.
class ChatRequest(BaseModel):
    # message는 사용자가 새로 입력한 질문입니다.
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="사용자가 입력한 새 질문",
        examples=["파이썬 FastAPI의 장점을 알려줘"],
    )

    # history는 이전 대화 내역입니다.
    # 기본값을 빈 리스트로 두어 첫 질문에서도 오류 없이 처리되게 합니다.
    history: List[ChatMessage] = Field(
        default_factory=list,
        description="이전 대화 내역",
    )

    # system_instruction은 챗봇의 역할과 답변 스타일을 지정하는 시스템 메시지입니다.
    # 값이 없으면 서비스 기본값을 사용합니다.
    system_instruction: Optional[str] = Field(
        default=None,
        description="챗봇 역할 지시문 (System Instruction)",
        examples=["너는 한국어로 친절하게 답변하는 AI 어시스턴트야."],
    )

    # 호출할 OpenAI 모델명입니다. 없으면 서버 환경 변수 기본값을 사용합니다.
    model: Optional[str] = Field(
        default=None,
        description="사용할 OpenAI 모델명",
        examples=["gpt-4o-mini", "gpt-4o", "o4-mini"],
    )

    # temperature는 답변의 창의성 정도입니다. o계열·gpt-5 모델은 지원하지 않습니다.
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="응답 다양성 (0~2). o계열/gpt-5 모델은 자동으로 무시됩니다.",
        examples=[0.7],
    )

    # top_p는 nucleus sampling 값입니다. temperature와 동시에 조정하는 것은 권장하지 않습니다.
    top_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling 값 (0~1)",
        examples=[1.0],
    )

    # max_output_tokens는 응답 최대 토큰 수입니다.
    max_output_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        description="응답 최대 토큰 수",
        examples=[1024],
    )


# 서버가 클라이언트에게 돌려줄 응답 데이터 구조입니다.
class ChatResponse(BaseModel):
    # reply는 ChatGPT 또는 데모 응답이 생성한 답변입니다.
    reply: str = Field(
        ...,
        description="챗봇 답변",
        examples=["FastAPI는 파이썬 기반의 빠른 웹 API 프레임워크입니다."],
    )

    # used_demo_mode는 실제 OpenAI API를 호출했는지, 데모 응답을 사용했는지 알려줍니다.
    # API 키가 없으면 True가 됩니다.
    used_demo_mode: bool = Field(
        default=False,
        description="OPENAI_API_KEY가 없어서 데모 응답을 사용했는지 여부",
    )
