(() => {
  if (document.getElementById('accessbridge-assistant')) return;
  const state = { fields: [], index: 0, recognition: null, active: false };
  const speak = (text) => {
    speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-IN'; utterance.rate = 0.88;
    speechSynthesis.speak(utterance);
    status.textContent = text;
  };
  const normalise = (text) => (text || '').replace(/\s+/g, ' ').trim();
  const labelFor = (field) => {
    const byFor = field.id && document.querySelector(`label[for="${CSS.escape(field.id)}"]`);
    const wrapping = field.closest('label');
    const nearby = field.closest('tr, .form-group, .field, div')?.innerText;
    return normalise(byFor?.innerText || wrapping?.innerText || field.getAttribute('aria-label') || field.name || field.placeholder || nearby || 'this field').slice(0, 180);
  };
  const discover = () => {
    state.fields = [...document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]), select, textarea')]
      .filter(f => !f.disabled && f.offsetParent !== null)
      .map(element => ({ element, label: labelFor(element) }))
      .filter(f => !/captcha|otp|password|aadhaar|submit|reset/i.test(f.label));
    state.index = Math.min(state.index, Math.max(0, state.fields.length - 1));
    count.textContent = `${state.fields.length} accessible form fields found`;
    return state.fields.length;
  };
  const current = () => state.fields[state.index];
  const announce = () => {
    const field = current();
    if (!field) return speak('No supported form fields were found on this page. Use the official portal controls directly.');
    field.element.focus({ preventScroll: false });
    field.element.classList.add('accessbridge-focus');
    setTimeout(() => field.element.classList.remove('accessbridge-focus'), 1800);
    const type = field.element.tagName === 'SELECT' ? 'Choose an option.' : 'Say your answer, or type it.';
    speak(`Field ${state.index + 1} of ${state.fields.length}. ${field.label}. ${type} Say next to continue, back to return, repeat to hear this again, or stop to pause.`);
  };
  const fill = (value) => {
    const field = current(); if (!field) return;
    const el = field.element;
    if (el.tagName === 'SELECT') {
      const option = [...el.options].find(o => normalise(o.text).toLowerCase().includes(value.toLowerCase()));
      if (option) el.value = option.value;
      else return speak(`I could not find ${value} in the available options. Please choose one with the keyboard or mouse.`);
    } else el.value = value;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    speak(`Entered ${value}. Say next when you are ready.`);
  };
  const command = (spoken) => {
    const text = normalise(spoken).toLowerCase();
    heard.textContent = `Heard: ${spoken}`;
    if (/^(next|continue|go ahead)/.test(text)) { state.index = Math.min(state.index + 1, state.fields.length - 1); announce(); }
    else if (/^(back|previous)/.test(text)) { state.index = Math.max(state.index - 1, 0); announce(); }
    else if (/^(repeat|again)/.test(text)) announce();
    else if (/^(stop|pause)/.test(text)) stopListening();
    else fill(spoken);
  };
  const stopListening = () => { state.active = false; state.recognition?.stop(); listen.textContent = 'Start voice guide'; speak('Voice guide paused.'); };
  const startListening = () => {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) return speak('Speech recognition is unavailable in this browser. Use Chrome or Edge, or type your answers.');
    discover(); state.recognition = new Recognition(); state.recognition.lang = 'en-IN'; state.recognition.continuous = true; state.recognition.interimResults = false;
    state.recognition.onresult = e => command(e.results[e.results.length - 1][0].transcript);
    state.recognition.onerror = e => { status.textContent = e.error === 'not-allowed' ? 'Allow microphone permission in the address bar, then restart voice guide.' : `Voice guide error: ${e.error}`; state.active = false; listen.textContent = 'Start voice guide'; };
    state.recognition.onend = () => { if (state.active) try { state.recognition.start(); } catch (_) {} };
    state.active = true; listen.textContent = 'Pause voice guide'; state.recognition.start(); announce();
  };
  const host = document.createElement('section'); host.id = 'accessbridge-assistant'; host.setAttribute('aria-label', 'AccessBridge portal assistant');
  host.innerHTML = `<div class="ab-head"><strong>AccessBridge</strong><button aria-label="Minimise assistant" id="ab-minimise">−</button></div><p id="ab-count">Ready to scan this form.</p><p id="ab-status" aria-live="polite">Select Start voice guide to begin.</p><p id="ab-heard" aria-live="polite"></p><div class="ab-actions"><button id="ab-start">Start voice guide</button><button id="ab-repeat">Repeat field</button><button id="ab-next">Next field</button></div><small>AccessBridge never completes OTP, CAPTCHA, payment, or final submission. You stay in control.</small>`;
  document.body.append(host);
  const status = host.querySelector('#ab-status'), count = host.querySelector('#ab-count'), heard = host.querySelector('#ab-heard'), listen = host.querySelector('#ab-start');
  listen.onclick = () => state.active ? stopListening() : startListening();
  host.querySelector('#ab-repeat').onclick = () => { discover(); announce(); };
  host.querySelector('#ab-next').onclick = () => { discover(); state.index = Math.min(state.index + 1, state.fields.length - 1); announce(); };
  host.querySelector('#ab-minimise').onclick = () => host.classList.toggle('ab-collapsed');
  discover();
})();
