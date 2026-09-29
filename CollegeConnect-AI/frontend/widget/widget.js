(function () {
  // Locate script tag and configuration attributes
  const currentScript = document.currentScript || (function () {
    const scripts = document.getElementsByTagName('script');
    return scripts[scripts.length - 1];
  })();

  const API_URL = (currentScript && currentScript.getAttribute('data-api-url')) || 'http://localhost:8000';
  const COLLEGE_NAME = (currentScript && currentScript.getAttribute('data-college-name')) || 'VVCE';

  // Inject CSS stylesheet
  const scriptSrc = currentScript && currentScript.src;
  const basePath = scriptSrc ? scriptSrc.substring(0, scriptSrc.lastIndexOf('/')) : '.';
  const linkId = 'collegeconnect-widget-style';
  if (!document.getElementById(linkId)) {
    const link = document.createElement('link');
    link.id = linkId;
    link.rel = 'stylesheet';
    link.href = basePath + '/widget.css';
    document.head.appendChild(link);
  }

  // Create Container
  const container = document.createElement('div');
  container.id = 'collegeconnect-widget-container';
  container.innerHTML = `
    <!-- Launcher Button -->
    <button class="cc-launcher-btn" id="ccLauncherBtn" title="Chat with VVCE Assistant" aria-label="Open Chat">
      <svg viewBox="0 0 24 24">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
      </svg>
    </button>

    <!-- Chat Window -->
    <div class="cc-chat-window" id="ccChatWindow" role="dialog" aria-modal="true" aria-hidden="true">
      <!-- Header -->
      <div class="cc-header">
        <div class="cc-header-info">
          <div class="cc-avatar">${COLLEGE_NAME.slice(0, 2)}</div>
          <div class="cc-title-wrap">
            <div class="cc-title">${COLLEGE_NAME} Virtual Assistant</div>
            <div class="cc-subtitle">
              <span class="cc-online-dot"></span> Official College Connect
            </div>
          </div>
        </div>
        <div class="cc-header-actions">
          <button class="cc-header-btn" id="ccClearBtn" title="Clear Chat">
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
          </button>
          <button class="cc-header-btn" id="ccCloseBtn" title="Close Window">
            <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24"><path d="M19 13H5v-2h14v2z"/></svg>
          </button>
        </div>
      </div>

      <!-- Messages Area -->
      <div class="cc-messages" id="ccMessages">
        <div class="cc-msg bot">
          Hello! I am your official <strong>${COLLEGE_NAME}</strong> assistant. Ask me about admissions, cut-off ranks, departments, regulations, or facilities.
          <div class="cc-quick-chips">
            <button class="cc-chip" data-q="What undergraduate B.E. programs are offered?">B.E. Programs</button>
            <button class="cc-chip" data-q="What are the cutoff ranks for admission?">Cutoff Ranks</button>
            <button class="cc-chip" data-q="How do I contact VVCE admissions?">Contact Info</button>
            <button class="cc-chip" data-q="Tell me about Computer Science and Engineering.">CSE Dept</button>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <form class="cc-input-wrap" id="ccChatForm">
        <input type="text" class="cc-input" id="ccInput" placeholder="Ask a question about ${COLLEGE_NAME}..." autocomplete="off" required />
        <button type="submit" class="cc-send-btn" id="ccSendBtn" aria-label="Send message">
          <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </form>
    </div>
  `;

  document.body.appendChild(container);

  // Element Selectors
  const launcherBtn = document.getElementById('ccLauncherBtn');
  const chatWindow = document.getElementById('ccChatWindow');
  const closeBtn = document.getElementById('ccCloseBtn');
  const clearBtn = document.getElementById('ccClearBtn');
  const chatForm = document.getElementById('ccChatForm');
  const chatInput = document.getElementById('ccInput');
  const messagesBox = document.getElementById('ccMessages');
  const sendBtn = document.getElementById('ccSendBtn');

  // Window State Toggle
  function toggleChat(open) {
    const isOpen = open !== undefined ? open : !chatWindow.classList.contains('open');
    chatWindow.classList.toggle('open', isOpen);
    chatWindow.setAttribute('aria-hidden', (!isOpen).toString());
    if (isOpen) {
      chatInput.focus();
    }
  }

  launcherBtn.addEventListener('click', () => toggleChat());
  closeBtn.addEventListener('click', () => toggleChat(false));

  clearBtn.addEventListener('click', () => {
    messagesBox.innerHTML = `
      <div class="cc-msg bot">
        Conversation cleared. How can I help you regarding <strong>${COLLEGE_NAME}</strong> today?
      </div>
    `;
  });

  // Quick Chips Click Event
  messagesBox.addEventListener('click', (e) => {
    if (e.target && e.target.classList.contains('cc-chip')) {
      const question = e.target.getAttribute('data-q');
      if (question) {
        chatInput.value = question;
        handleSendMessage();
      }
    }
  });

  // Markdown-like text formatter
  function formatMarkdown(text) {
    let html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/^- (.*)$/gm, '<li>$1</li>')
      .replace(/\n\n/g, '<br/><br/>')
      .replace(/\n/g, '<br/>');

    if (html.includes('<li>')) {
      html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
    }
    return html;
  }

  // Append Message
  function appendMessage(text, sender) {
    const msg = document.createElement('div');
    msg.className = `cc-msg ${sender}`;
    msg.innerHTML = sender === 'user' ? text : formatMarkdown(text);
    messagesBox.appendChild(msg);
    messagesBox.scrollTop = messagesBox.scrollHeight;
    return msg;
  }

  // Render Source Pills
  function renderSources(containerElem, sources) {
    if (!sources || sources.length === 0) return;
    const sourcesWrap = document.createElement('div');
    sourcesWrap.className = 'cc-sources';
    sourcesWrap.innerHTML = '<div class="cc-sources-title">Verified Official Sources:</div>';

    sources.forEach((s) => {
      const pill = document.createElement('a');
      pill.className = 'cc-source-pill';
      pill.href = s.url;
      pill.target = '_blank';
      pill.rel = 'noopener noreferrer';
      pill.textContent = '📄 ' + (s.title || 'VVCE Page');
      sourcesWrap.appendChild(pill);
    });

    containerElem.appendChild(sourcesWrap);
    messagesBox.scrollTop = messagesBox.scrollHeight;
  }

  // Handle Send Message & Stream
  async function handleSendMessage() {
    const query = chatInput.value.trim();
    if (!query) return;

    appendMessage(query, 'user');
    chatInput.value = '';
    sendBtn.disabled = true;

    // Placeholder bot bubble
    const botMsg = appendMessage('', 'bot');
    const cursor = document.createElement('span');
    cursor.className = 'cc-cursor';
    botMsg.appendChild(cursor);

    let fullText = '';
    let sources = [];

    try {
      const response = await fetch(`${API_URL}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query })
      });

      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please wait a moment before sending another message.');
        }
        throw new Error(`Server returned error (${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop(); // keep partial

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data:')) {
            try {
              const data = JSON.parse(trimmed.slice(5).trim());
              if (data.token) {
                fullText += data.token;
                botMsg.innerHTML = formatMarkdown(fullText);
                botMsg.appendChild(cursor);
                messagesBox.scrollTop = messagesBox.scrollHeight;
              }
              if (data.sources && data.sources.length > 0) {
                sources = data.sources;
              }
            } catch (err) {
              console.warn('Error parsing SSE token:', err);
            }
          }
        }
      }

      // Remove cursor
      if (cursor.parentNode) cursor.remove();
      botMsg.innerHTML = formatMarkdown(fullText);

      // Render citations
      if (sources && sources.length > 0) {
        renderSources(botMsg, sources);
      }

    } catch (err) {
      if (cursor.parentNode) cursor.remove();
      botMsg.innerHTML = `<span style="color:#DC2626;">Error: ${err.message || 'Unable to connect to CollegeConnect server.'}</span>`;
    } finally {
      sendBtn.disabled = false;
      messagesBox.scrollTop = messagesBox.scrollHeight;
    }
  }

  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    handleSendMessage();
  });

})();
