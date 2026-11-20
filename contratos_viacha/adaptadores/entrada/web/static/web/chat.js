/* Ventana del chatbot. Los mensajes se escriben con textContent: nunca se interpreta HTML. */
(function () {
  const script = document.currentScript;
  const urlConsultar = script.dataset.urlConsultar, urlSubir = script.dataset.urlSubir;
  const $ = (id) => document.getElementById(id);
  const csrf = () => document.querySelector('meta[name="csrf-token"]').content;
  const panel = $('chat'), msgs = $('chat-msgs'), texto = $('chat-texto'), fab = $('chat-abrir');
  let archivo = null, saludo = false;

  function burbuja(cls, contenido, pie) {
    const d = document.createElement('div');
    d.className = 'burbuja ' + cls;
    d.textContent = contenido;
    if (pie) { const s = document.createElement('small'); s.textContent = pie; d.appendChild(s); }
    msgs.appendChild(d); msgs.scrollTop = msgs.scrollHeight; return d;
  }
  function abrir() {
    panel.hidden = false; fab.hidden = true; texto.focus();
    if (!saludo) { saludo = true; burbuja('bot', 'Hola. Soy el asistente de contratos. Pregúntame, por ejemplo: «¿Qué vence esta semana?» o «¿Cómo está el contrato 045/2026?». Escribe «ayuda» para ver todo lo que puedo hacer.'); }
  }
  function cerrar() { panel.hidden = true; fab.hidden = false; }

  async function enviar() {
    const m = texto.value.trim(); if (!m) return;
    texto.value = ''; burbuja('yo', m);
    const espera = burbuja('bot', 'Consultando…');
    try {
      const r = await fetch(urlConsultar, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() }, body: JSON.stringify({ mensaje: m }) });
      const d = await r.json();
      espera.remove();
      if (!r.ok) { burbuja('bot', d.error || 'No pude procesar la consulta.'); return; }
      burbuja('bot', d.texto, d.adaptador && d.adaptador !== 'plantillas' ? 'Redactado con ' + d.adaptador : '');
    } catch (e) { espera.remove(); burbuja('bot', 'No hay conexión con el servidor. Inténtalo de nuevo.'); }
  }

  async function subir() {
    const numero = $('chat-numero').value.trim();
    if (!archivo || !numero) { burbuja('bot', 'Indica el número del contrato (por ejemplo 045/2026) para adjuntar el archivo.'); return; }
    const fd = new FormData(); fd.append('archivo', archivo); fd.append('numero', numero);
    const espera = burbuja('bot', 'Subiendo «' + archivo.name + '»…');
    try {
      const r = await fetch(urlSubir, { method: 'POST', headers: { 'X-CSRFToken': csrf() }, body: fd });
      const d = await r.json(); espera.remove();
      burbuja('bot', r.ok ? d.texto : (d.error || 'No se pudo subir el archivo.'));
      if (r.ok) limpiar();
    } catch (e) { espera.remove(); burbuja('bot', 'No se pudo subir el archivo. Revisa la conexión.'); }
  }
  function limpiar() { archivo = null; $('chat-file').value = ''; $('chat-numero').value = ''; $('chat-adjunto').hidden = true; }

  fab.addEventListener('click', abrir); $('chat-cerrar').addEventListener('click', cerrar);
  $('chat-enviar').addEventListener('click', enviar);
  texto.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); enviar(); } });
  $('chat-clip').addEventListener('click', () => $('chat-file').click());
  $('chat-file').addEventListener('change', (e) => {
    archivo = e.target.files[0] || null; if (!archivo) return;
    $('chat-archivo').textContent = archivo.name; $('chat-adjunto').hidden = false; $('chat-numero').focus();
  });
  $('chat-subir').addEventListener('click', subir); $('chat-cancelar').addEventListener('click', limpiar);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !panel.hidden) cerrar(); });
})();
