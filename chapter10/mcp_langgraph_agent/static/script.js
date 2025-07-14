document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatBox = document.getElementById("chat-box");

  // 페이지 로드 시 고유한 세션 ID 생성
  const sessionId =
    "session_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
  console.log("새로운 세션 ID:", sessionId);

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = chatInput.value;
    if (!message) return;

    appendMessage("user", message);
    chatInput.value = "";

    // 봇 메시지를 위한 div를 만들고 스트리밍 시작
    const botMessageElement = createMessageElement("bot");
    await streamResponse(message, botMessageElement);
  });

  async function streamResponse(message, botMessageElement) {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        message: message,
        session_id: sessionId,
      }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let content = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      content += decoder.decode(value, { stream: true });
      botMessageElement.innerHTML = marked.parse(content);
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  }

  function createMessageElement(sender) {
    const messageElement = document.createElement("div");
    messageElement.classList.add(
      "message",
      sender === "user" ? "user-message" : "bot-message"
    );
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
    return messageElement;
  }

  function appendMessage(sender, text) {
    const messageElement = createMessageElement(sender);
    messageElement.innerHTML = marked.parse(text);
  }

  // marked.js 설정: 링크가 새창에서 열리도록 설정
  const renderer = {
    link(href, title, text) {
      const link = marked.Renderer.prototype.link.call(this, href, title, text);
      return link.replace("<a", "<a target='_blank' rel='noreferrer' ");
    },
  };

  marked.use({
    renderer,
  });
});
