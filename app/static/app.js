// app/static/app.js
// ------------------------------------------------------------
// 챗봇 화면의 동작을 담당하는 JavaScript 파일입니다.
// 사용자의 입력을 FastAPI /api/chat 엔드포인트로 전송하고 응답을 화면에 출력합니다.
// ------------------------------------------------------------

// 챗봇 열기 버튼 요소를 가져옵니다.
const chatIcon = document.getElementById("chatIcon");
const chatModal = document.getElementById("chatModal");
const closeChat = document.getElementById("closeChat");
const chatMessages = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");

// 설정 패널 관련 요소를 가져옵니다.
const toggleSettings = document.getElementById("toggleSettings");
const clearHistory = document.getElementById("clearHistory");
const settingsPanel = document.getElementById("settingsPanel");
const systemInstruction = document.getElementById("systemInstruction");
const modelSelect = document.getElementById("modelSelect");
const temperatureInput = document.getElementById("temperatureInput");
const topPInput = document.getElementById("topPInput");
const maxTokensInput = document.getElementById("maxTokensInput");
const tempWarning = document.getElementById("tempWarning");

// temperature를 지원하지 않는 모델 접두사 목록입니다.
// 서버와 동일한 규칙을 프론트에서도 유지하여 즉시 경고를 표시합니다.
const NO_TEMPERATURE_PREFIXES = ["o1", "o2", "o3", "o4", "o5", "gpt-5"];

// 이전 대화 내역을 저장하는 배열입니다.
const history = [];

// 선택한 모델이 temperature를 지원하는지 확인하는 함수입니다.
function supportsTemperature(modelName) {
    if (!modelName) return true;
    const lower = modelName.toLowerCase();
    return !NO_TEMPERATURE_PREFIXES.some((prefix) => lower.startsWith(prefix));
}

// 모델 선택이 바뀔 때 temperature 입력창 활성화 여부와 경고를 갱신합니다.
modelSelect.addEventListener("change", () => {
    const ok = supportsTemperature(modelSelect.value);
    temperatureInput.disabled = !ok;
    tempWarning.classList.toggle("hidden", ok);
    if (!ok) temperatureInput.value = "";
});

// 설정 버튼 클릭 시 설정 패널을 열고 닫습니다.
toggleSettings.addEventListener("click", () => {
    settingsPanel.classList.toggle("hidden");
});

// 대화 초기화 버튼 클릭 시 화면과 내역을 모두 지웁니다.
clearHistory.addEventListener("click", () => {
    history.length = 0;
    chatMessages.innerHTML = "";
});

// 챗봇 버튼을 클릭하면 모달을 표시합니다.
chatIcon.addEventListener("click", () => {
    chatModal.classList.remove("hidden");
    messageInput.focus();
});

// 닫기 버튼을 클릭하면 모달을 숨깁니다.
closeChat.addEventListener("click", () => {
    chatModal.classList.add("hidden");
});

// 화면에 메시지 말풍선을 추가하는 함수입니다.
function addMessage(role, content) {
    const messageElement = document.createElement("div");
    messageElement.className = `message ${role}`;
    // textContent를 사용하여 XSS를 방지합니다.
    messageElement.textContent = content;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return messageElement;
}

// 설정 패널에서 현재 값을 읽어 API 요청 바디를 구성하는 함수입니다.
function buildRequestBody(message) {
    const body = {
        message,
        history: history.slice(0, -1),
    };

    const instruction = systemInstruction.value.trim();
    if (instruction) body.system_instruction = instruction;

    const model = modelSelect.value;
    if (model) body.model = model;

    // temperature는 모델이 지원할 때만 포함합니다.
    if (supportsTemperature(model)) {
        const temp = temperatureInput.value.trim();
        if (temp !== "") body.temperature = parseFloat(temp);
    }

    const topP = topPInput.value.trim();
    if (topP !== "") body.top_p = parseFloat(topP);

    const maxTokens = maxTokensInput.value.trim();
    if (maxTokens !== "") body.max_output_tokens = parseInt(maxTokens, 10);

    return body;
}

// 메시지 전송 폼이 제출될 때 실행되는 이벤트입니다.
chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = messageInput.value.trim();
    if (!message) return;

    addMessage("user", message);
    history.push({ role: "user", content: message });
    messageInput.value = "";

    const loadingMessage = addMessage("assistant", "답변을 생성하는 중입니다...");

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(buildRequestBody(message)),
        });

        if (!response.ok) {
            throw new Error(`서버 오류: ${response.status}`);
        }

        const data = await response.json();
        loadingMessage.textContent = data.reply;
        history.push({ role: "assistant", content: data.reply });
    } catch (error) {
        loadingMessage.textContent = `오류가 발생했습니다. ${error.message}`;
    }
});
