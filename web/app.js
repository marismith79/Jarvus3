const chatContainer = document.getElementById('chat-container');
const form = document.getElementById('chat-form');
const input = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

function el(tag, className, text) {
  const e = document.createElement(tag);
  if (className) e.className = className;
  if (text !== undefined) e.textContent = text;
  return e;
}

function addMessage(role, text, meta) {
  const wrap = el('div', 'msg');
  const avatar = el('div', `avatar ${role}`);
  avatar.textContent = role === 'user' ? 'U' : 'K';
  const bubbleWrap = el('div');
  const bubble = el('div', 'bubble');
  bubble.textContent = text;
  bubbleWrap.appendChild(bubble);
  if (meta) {
    const metaBubble = el('div', 'bubble meta');
    metaBubble.textContent = meta;
    bubbleWrap.appendChild(metaBubble);
  }
  wrap.appendChild(avatar);
  wrap.appendChild(bubbleWrap);
  chatContainer.appendChild(wrap);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function sendMessage(message) {
  addMessage('user', message);
  sendBtn.disabled = true;
  input.value = '';

  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    if (!resp.ok) {
      const { detail } = await resp.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(detail || 'Request failed');
    }
    const data = await resp.json();
    const meta = `Cypher: ${data.cypher}`;
    addMessage('bot', data.answer, meta);
  } catch (err) {
    addMessage('bot', 'Sorry, something went wrong.', String(err), true);
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener('submit', (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (message) sendMessage(message);
});

input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && e.shiftKey) {
    // allow newline
    return;
  }
  if (e.key === 'Enter') {
    e.preventDefault();
    form.requestSubmit();
  }
});


