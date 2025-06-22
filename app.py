<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Alia - Tu Asistente IA</title>
  <!-- Fragmento de AdSense para verificación de propiedad -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9787034270648228"
    crossorigin="anonymous"></script>
  <!-- ads.txt como comentario informativo, el archivo real debe estar en la raíz pública -->
  <!-- google.com, pub-9787034270648228, DIRECT, f08c47fec0942fa0 -->
  <!-- Estilos y fuentes -->
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}" />

  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" />
  <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500&family=Fira+Mono&family=Roboto:wght@300;400;500&family=Open+Sans:wght@300;400;500&family=Inter:wght@300;400;500&family=Lato:wght@300;400&family=Raleway:wght@300;400;500&family=Montserrat:wght@300;400;500&family=Nunito:wght@300;400;500&family=Oswald:wght@300;400;500&family=Ubuntu:wght@300;400;500&family=Poppins:wght@300;400;500&family=Quicksand:wght@300;400;500&family=Playfair+Display:wght@400;500&family=Merriweather:wght@300;400&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/emoji-picker-element@^1/index.js" type="module"></script>
  <style>
    #galleryBtn {
      background: #432878;
      color: #fff;
      border: none;
      border-radius: 50%;
      width: 44px; height: 44px;
      font-size: 1.25em;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-left: 5px;
      cursor: pointer;
      box-shadow: 0 1px 6px #0002;
      transition: all 0.3s ease;
    }
    #galleryBtn:hover {
      background: #5a3a9a;
      transform: scale(1.05);
    }
    #imgStatus {
      display: block;
      font-size: 0.98em;
      color: #aaa;
      margin: 4px 0 0 0;
      text-align: left;
      padding-left: 10px;
      min-height: 20px;
    }
    #chatForm {
      display: flex;
      align-items: center;
      gap: 8px;
      position: relative;
      background: none;
      border: none;
      width: 100%;
      box-sizing: border-box;
    }
    #previewContainer {
      display: none;
      flex-shrink: 0;
      align-items: center;
      gap: 4px;
      margin: 0 0 10px 0;
      padding: 10px;
      max-height: 64px;
      min-height: 0;
      height: auto;
      width: 100%;
      box-sizing: border-box;
      position: relative;
      z-index: 1;
      background: var(--input-bg);
      border-radius: 12px;
      border: 1px solid var(--border-color);
      order: -1;
    }
    #imgPreview {
      max-width: 44px;
      max-height: 44px;
      width: 44px;
      height: 44px;
      border-radius: 9px;
      box-shadow: 0 0 6px #0003;
      border: 2px solid #432878;
      background: #201e38;
      object-fit: cover;
      display: block;
    }
    #clearPreviewBtn {
      background: #d7263d;
      color: white;
      border: none;
      border-radius: 50%;
      width: 22px;
      height: 22px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1em;
      margin-left: 0;
      position: absolute;
      top: 2px;
      left: 32px;
      z-index: 2;
      padding: 0;
    }

    .audio-recording {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      width: 100vw;
      height: 80px;
      background: var(--bg-color);
      border-top: 2px solid var(--primary-color);
      padding: 15px;
      display: none;
      align-items: center;
      justify-content: center;
      gap: 15px;
      z-index: 9999;
      box-shadow: 0 -4px 20px rgba(0,0,0,0.3);
      margin: 0;
      box-sizing: border-box;
    }
    
    .audio-recording::before {
      content: '';
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      height: 100px;
      background: var(--bg-color);
      z-index: -1;
    }
    .audio-wave {
      flex: 1;
      height: 40px;
      background: var(--input-bg);
      border-radius: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
    }
    .wave-bars {
      display: flex;
      align-items: center;
      gap: 2px;
      height: 100%;
    }
    .wave-bar {
      width: 3px;
      background: var(--primary-color);
      border-radius: 2px;
      animation: wave 1.5s infinite ease-in-out;
    }
    .wave-bar:nth-child(2) { animation-delay: 0.1s; }
    .wave-bar:nth-child(3) { animation-delay: 0.2s; }
    .wave-bar:nth-child(4) { animation-delay: 0.3s; }
    .wave-bar:nth-child(5) { animation-delay: 0.4s; }
    .audio-timer {
      position: absolute;
      right: 15px;
      color: var(--text-color);
      font-size: 14px;
      font-weight: 500;
    }
    .audio-cancel, .audio-send {
      width: 50px;
      height: 50px;
      border-radius: 50%;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      cursor: pointer;
      transition: all 0.3s ease;
    }
    .audio-cancel {
      background: #ff4444;
      color: white;
    }
    .audio-send {
      background: var(--primary-color);
      color: white;
    }
    .audio-cancel:hover { background: #cc0000; }
    .audio-send:hover { background: var(--primary-hover); }

    .send-btn.recording {
      background: #ff4444 !important;
      animation: pulse-red 1s infinite;
    }
    .send-btn.recording .send-icon,
    .send-btn.recording .stop-icon { display: none !important; }
    .send-btn.recording .audio-icon { display: block !important; }

    @keyframes wave {
      0%, 100% { height: 10px; }
      50% { height: 30px; }
    }
    @keyframes pulse-red {
      0% { box-shadow: 0 0 0 0 rgba(255, 68, 68, 0.7); }
      70% { box-shadow: 0 0 0 10px rgba(255, 68, 68, 0); }
      100% { box-shadow: 0 0 0 0 rgba(255, 68, 68, 0); }
    }

    /* Audio Player */
    .audio-message {
      display: flex;
      align-items: center;
      gap: 10px;
      background: var(--input-bg);
      padding: 10px 15px;
      border-radius: 20px;
      margin: 5px 0;
      max-width: 300px;
    }
    .audio-play-btn {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: var(--primary-color);
      color: white;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 16px;
    }
    .audio-progress {
      flex: 1;
      height: 4px;
      background: var(--border-color);
      border-radius: 2px;
      position: relative;
      cursor: pointer;
    }
    .audio-progress-bar {
      height: 100%;
      background: var(--primary-color);
      border-radius: 2px;
      width: 0%;
      transition: width 0.1s;
    }
    .audio-duration {
      font-size: 12px;
      color: var(--text-secondary);
      min-width: 35px;
    }

    @media (max-width: 600px) {
      .audio-recording {
        padding: 10px;
        gap: 10px;
      }
      .audio-cancel, .audio-send {
        width: 45px;
        height: 45px;
        font-size: 18px;
      }
      .audio-wave {
        height: 35px;
      }
    }

    /* Modal de Voz */
    .voice-modal {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.8);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
    }
    .voice-modal-content {
      background: var(--bg-color);
      border-radius: 20px;
      padding: 30px;
      text-align: center;
      max-width: 400px;
      width: 90%;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
      border: 2px solid var(--primary-color);
      margin: 0 auto;
      position: relative;
    }
    .voice-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }
    .voice-header h3 {
      margin: 0;
      color: var(--primary-color);
    }
    .voice-close-btn {
      background: none;
      border: none;
      font-size: 24px;
      color: var(--text-color);
      cursor: pointer;
      padding: 0;
      width: 30px;
      height: 30px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .voice-animation {
      position: relative;
      margin: 20px 0;
    }
    .voice-circle {
      width: 80px;
      height: 80px;
      border-radius: 50%;
      background: var(--primary-color);
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      z-index: 2;
    }
    .voice-circle::before {
      content: '';
      font-family: 'Font Awesome 6 Free';
      font-weight: 900;
      color: white;
      font-size: 24px;
    }
    .voice-waves {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
    }
    .wave {
      position: absolute;
      border: 2px solid var(--primary-color);
      border-radius: 50%;
      opacity: 0;
    }
    .voice-modal-content.listening .wave {
      animation: pulse 2s infinite;
    }
    .wave:nth-child(1) {
      width: 100px;
      height: 100px;
      margin: -50px 0 0 -50px;
    }
    .wave:nth-child(2) {
      width: 120px;
      height: 120px;
      margin: -60px 0 0 -60px;
      animation-delay: 0.3s;
    }
    .wave:nth-child(3) {
      width: 140px;
      height: 140px;
      margin: -70px 0 0 -70px;
      animation-delay: 0.6s;
    }
    .voice-modal-content.speaking .voice-circle {
      background: #4caf50;
      animation: speaking 1s infinite alternate;
    }
    .voice-modal-content.speaking .voice-circle::before {
      content: '';
    }
    .voice-text {
      margin: 20px 0 0 0;
      color: var(--text-color);
      font-size: 16px;
    }
    @keyframes pulse {
      0% {
        transform: scale(0.8);
        opacity: 1;
      }
      100% {
        transform: scale(1.2);
        opacity: 0;
      }
    }
    @keyframes speaking {
      0% {
        transform: scale(1);
      }
      100% {
        transform: scale(1.1);
      }
    }
    @media (max-width: 600px) {
      #galleryBtn { width:36px; height:36px; font-size:1.05em;}
      .voice-modal-content {
        padding: 20px;
        max-width: 350px;
      }
      .voice-circle {
        width: 60px;
        height: 60px;
      }
      .voice-circle::before {
        font-size: 18px;
      }
      .wave:nth-child(1) {
        width: 80px;
        height: 80px;
        margin: -40px 0 0 -40px;
      }
      .wave:nth-child(2) {
        width: 100px;
        height: 100px;
        margin: -50px 0 0 -50px;
      }
      .wave:nth-child(3) {
        width: 120px;
        height: 120px;
        margin: -60px 0 0 -60px;
      }
      #previewContainer {
        max-height: 36px;
        position: absolute;
        left: 0;
        right: 0;
        bottom: 62px; /* Altura de la barra de entrada + margen */
        margin: 0 auto;
        max-width: 98vw;
        z-index: 10;
        border-radius: 10px;
        background: var(--input-bg);
        box-shadow: 0 2px 12px #0002;
        padding: 8px 10px;
        display: flex;
        align-items: center;
      }
      #imgPreview { max-width: 36px; max-height: 36px; width:36px; height:36px;}
      #clearPreviewBtn { width:17px; height:17px; font-size:0.9em; left:25px; }
      .chat-form { position: relative; }
    }

    /* Estilos para imágenes en el chat */
    .message-content img {
      transition: transform 0.2s ease;
      border: 2px solid var(--border-color);
    }
    .message-content img:hover {
      transform: scale(1.02);
      border-color: var(--primary-color);
    }
    .message.user .message-content img {
      border-color: var(--primary-color);
    }
    @media (max-width: 600px) {
      .message-content img {
        max-width: 200px !important;
        max-height: 150px !important;
      }
    }
  </style>
</head>
<body class="dark-theme purple-theme">

<!-- Modal de aviso historial -->
<div id="historialAvisoModal" class="modal-aviso" style="display:none;">
  <div class="modal-aviso-content">
    <h3><i class="fas fa-info-circle"></i> Importante</h3>
    <p>
      Actualmente, el historial de chat se guarda de forma local en este dispositivo.<br>
      Esto significa que tus conversaciones no se comparten ni están disponibles al iniciar sesión desde otros dispositivos o navegadores.<br>
      Te recomendamos exportar la información que consideres relevante antes de cambiar de equipo.
    </p>
    <button id="cerrarAvisoBtn" class="btn btn-primary">Entendido</button>
    <label style="display:block; margin-top:10px;">
      <input type="checkbox" id="noMostrarAvisoCheck"> No mostrar este mensaje nuevamente
    </label>
  </div>
</div>

<!-- Sidebar -->
<button id="sidebarBtn" class="sidebar-btn">
  <span class="icon-bar"></span>
  <span class="icon-bar"></span>
  <span class="icon-bar"></span>
</button>

<div id="sidebar" class="sidebar">
  <div class="sidebar-header">
    <h2><i class="fas fa-history"></i> Historial</h2>
    <button id="closeSidebarBtn" class="close-sidebar-btn">×</button>
  </div>
  <input type="text" id="searchChatInput" placeholder="Buscar chats...">
  <ul id="chatList">
    <li class="new-chat-item">
      <button id="newChatBtn" class="new-chat-btn">
        <i class="fas fa-plus"></i> Nuevo Chat
      </button>
      <button id="tempChatBtn" class="temp-chat-btn">
        <i class="fas fa-clock"></i> Chat Temporal
      </button>
    </li>
  </ul>
</div>

<!-- Contenido Principal -->
<div class="chat-container">
  <div class="main-chat">
    <header class="chat-header">
      <div></div>
      <div class="header-center">
        <div class="alia-icon-wrapper">
          <img src="{{ url_for('static', filename='logo.png') }}" alt="Logo Alia" class="logo-ia">
        </div>
        <h1>Alia</h1>
      </div>
      <div class="settings-menu">
        <button class="settings-btn" id="settingsButton">
          <i class="fas fa-ellipsis-v"></i>
        </button>
        <div class="settings-dropdown">
          <div class="settings-section">
            <span class="settings-label">Tema</span>
            <div class="theme-toggle">
              <button class="theme-btn dark" data-theme="dark"><i class="fas fa-moon"></i> Oscuro</button>
              <button class="theme-btn light" data-theme="light"><i class="fas fa-sun"></i> Claro</button>
            </div>
          </div>
          <div class="settings-section">
            <span class="settings-label">Color</span>
            <div class="color-palette">
              <button class="color-btn purple" data-color="purple" title="Púrpura"></button>
              <button class="color-btn blue" data-color="blue" title="Azul"></button>
              <button class="color-btn green" data-color="green" title="Verde"></button>
              <button class="color-btn red" data-color="red" title="Rojo"></button>
              <button class="color-btn orange" data-color="orange" title="Naranja"></button>
              <button class="color-btn pink" data-color="pink" title="Rosa"></button>
              <button class="color-btn teal" data-color="teal" title="Turquesa"></button>
            </div>
          </div>
          <div class="settings-section">
            <span class="settings-label">Fuente</span>
            <div id="fontSelectorBtn" class="font-selector-btn">Selecciona una fuente</div>
          </div>
          <div class="settings-section">
            <span class="settings-label">Idioma</span>
            <select id="lang-selector">
              <option value="es">Español</option>
              <option value="en">English</option>
              <option value="fr">Français</option>
            </select>
          </div>

          <div style="margin-top: 15px; border-top: 1px solid var(--border-color); padding-top: 10px;">
            <button id="btnLogout" class="logout-btn">
              <i class="fas fa-sign-out-alt"></i> Cerrar sesión
            </button>
          </div>
        </div>
        <div id="fontPanel" class="font-panel">
          <div class="font-panel-header">
            <span id="fontPanelTitle">Selecciona una fuente</span>
            <button id="closeFontPanel" class="close-font-panel-btn">&times;</button>
          </div>
          <ul class="font-list">
            <li style="font-family: 'Poppins', sans-serif;" data-font="Poppins, sans-serif">Poppins - Redondeada y moderna</li>
            <li style="font-family: 'Roboto', sans-serif;" data-font="Roboto, sans-serif">Roboto - Clásica de Google</li>
            <li style="font-family: 'Open Sans', sans-serif;" data-font="Open Sans, sans-serif">Open Sans - Neutral y legible</li>
            <li style="font-family: 'Inter', sans-serif;" data-font="Inter, sans-serif">Inter - Diseñada para UI</li>
            <li style="font-family: 'Lato', sans-serif;" data-font="Lato, sans-serif">Lato - Elegante y profesional</li>
            <li style="font-family: 'Raleway', sans-serif;" data-font="Raleway, sans-serif">Raleway - Estilizada y fina</li>
            <li style="font-family: 'Montserrat', sans-serif;" data-font="Montserrat, sans-serif">Montserrat - Geométrica</li>
            <li style="font-family: 'Nunito', sans-serif;" data-font="Nunito, sans-serif">Nunito - Suave y amigable</li>
            <li style="font-family: 'Oswald', sans-serif;" data-font="Oswald, sans-serif">Oswald - Condensada y fuerte</li>
            <li style="font-family: 'Ubuntu', sans-serif;" data-font="Ubuntu, sans-serif">Ubuntu - Humanista y cálida</li>
            <li style="font-family: 'Quicksand', sans-serif;" data-font="Quicksand, sans-serif">Quicksand - Moderna y limpia</li>
            <li style="font-family: 'Playfair Display', serif;" data-font="Playfair Display, serif">Playfair Display - Serif elegante</li>
            <li style="font-family: 'Merriweather', serif;" data-font="Merriweather, serif">Merriweather - Serif legible</li>
            <li style="font-family: 'Fira Code', monospace;" data-font="Fira Code, monospace">Fira Code - Monoespaciada</li>
          </ul>
        </div>

      </div>
    </header>

    <div id="chatBox" class="chat-box"></div>

    <!-- MINIATURA: fuera del form para evitar que la barra se oculte -->
    <div id="previewContainer">
      <div style="position: relative; display: inline-block;">
        <img id="imgPreview" src="" alt="Imagen a enviar">
        <button id="clearPreviewBtn" type="button" title="Quitar imagen">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div style="flex: 1; padding-left: 8px;">
        <span style="font-size: 0.9em; color: var(--text-color); opacity: 0.8;">
          📷 Imagen lista para análisis
        </span>
      </div>
    </div>

    <form id="chatForm" class="chat-form" autocomplete="off">
      <div class="input-row">
        <button type="button" class="emoji-btn" id="emojiButton">
          <i class="far fa-smile"></i>
        </button>
        <div class="input-wrapper">
          <input type="text" id="pregunta" name="pregunta" placeholder="Chatea con Alia..." autocomplete="off">
          <button type="submit" id="sendButton" class="send-btn" disabled>
            <i class="fas fa-paper-plane"></i>
          </button>
        </div>
        <!-- Botón de galería -->
        <input type="file" id="imgInput" name="file" accept="image/*" style="display:none;">
        <button type="button" id="galleryBtn" title="Enviar imagen desde galería">
          <i class="fas fa-image"></i>
        </button>

      </div>

    </form>
    <span id="imgStatus"></span>
    <emoji-picker id="emojiPicker"></emoji-picker>
  </div>
</div>

<!-- Panel Confirmación cerrar sesión -->
<div id="confirmLogoutPanel" style="display: none;">
  <div class="confirmation-box">
    <p>¿Estás seguro de que deseas cerrar sesión?</p>
    <div class="confirmation-buttons">
      <button id="confirmLogoutYes">Sí</button>
      <button id="confirmLogoutNo">No</button>
    </div>
  </div>
</div>

<!-- Panel Confirmación eliminar chat -->
<div id="confirmationPanel" style="display: none;">
  <div class="confirmation-box">
    <p>¿Estás seguro de que deseas eliminar este chat permanentemente?</p>
    <div class="confirmation-buttons">
      <button id="confirmDeleteBtn">Eliminar</button>
      <button id="cancelDeleteBtn">Cancelar</button>
    </div>
  </div>
</div>





<script src="https://cdn.socket.io/4.6.1/socket.io.min.js"></script>
<script>
  window.USER_EMAIL = "{{ session['email'] }}";
  const mostrarAvisoHistorial = {{ "true" if mostrar_aviso_historial else "false" }};
</script>
<script src="{{ url_for('static', filename='script.js') }}"></script>

<script>
  // Fuente personalizada (igual que antes)
  document.addEventListener('DOMContentLoaded', () => {


    // Fuente personalizada
    const fontItems = document.querySelectorAll('.font-list li');
    const fontSelectorBtn = document.getElementById('fontSelectorBtn');
    const savedFont = localStorage.getItem('chatFont');
    if (savedFont) {
      document.body.style.fontFamily = savedFont;
      fontItems.forEach(item => {
        item.classList.remove('selected');
        if (item.dataset.font === savedFont) {
          item.classList.add('selected');
          if (fontSelectorBtn) fontSelectorBtn.textContent = item.textContent;
        }
      });
    }
    fontItems.forEach(item => {
      item.addEventListener('click', () => {
        const selectedFont = item.dataset.font;
        document.body.style.fontFamily = selectedFont;
        localStorage.setItem('chatFont', selectedFont);
        fontItems.forEach(i => i.classList.remove('selected'));
        item.classList.add('selected');
        if (fontSelectorBtn) fontSelectorBtn.textContent = item.textContent;
        const panel = document.getElementById('fontPanel');
        if (panel) panel.style.display = 'none';
      });
    });
    const closeFontPanel = document.getElementById('closeFontPanel');
    if (closeFontPanel) {
      closeFontPanel.addEventListener('click', () => {
        const panel = document.getElementById('fontPanel');
        if (panel) panel.style.display = 'none';
      });
    }
    const openFontPanelBtn = document.getElementById('fontSelectorBtn');
    if (openFontPanelBtn) {
      openFontPanelBtn.addEventListener('click', () => {
        const panel = document.getElementById('fontPanel');
        if (panel) panel.style.display = 'block';
      });
    }
  });

  // Manejo unificado de imágenes
  document.addEventListener('DOMContentLoaded', () => {
    const galleryBtn = document.getElementById('galleryBtn');
    const imgInput = document.getElementById('imgInput');
    const imgStatus = document.getElementById('imgStatus');
    const previewContainer = document.getElementById('previewContainer');
    const imgPreview = document.getElementById('imgPreview');
    const clearPreviewBtn = document.getElementById('clearPreviewBtn');
    const preguntaInput = document.getElementById('pregunta');

    // Función para limpiar preview
    window.clearImagePreview = function() {
      if (imgInput) imgInput.value = '';
      if (previewContainer) previewContainer.style.display = "none";
      if (imgPreview) imgPreview.src = '';
      if (imgStatus) imgStatus.textContent = '';
      updateSendButton();
    };

    // Seleccionar imagen y mostrar miniatura inmediatamente
    if (galleryBtn && imgInput) {
      galleryBtn.onclick = () => imgInput.click();

      imgInput.addEventListener('change', function() {
        if (this.files && this.files.length > 0) {
          const file = this.files[0];

          // Validaciones mejoradas para imágenes de cámara
          const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];

          // Si no tiene tipo definido pero es imagen, asignar JPEG por defecto
          if (!file.type && file.name && /\.(jpe?g|png|gif|webp)$/i.test(file.name)) {
            Object.defineProperty(file, 'type', {
              value: 'image/jpeg',
              writable: false
            });
          }

          if (file.type && !allowedTypes.includes(file.type)) {
            showNotification('❌ Tipo de archivo no soportado. Usa: JPG, PNG, GIF o WebP');
            clearImagePreview();
            return;
          }

          if (file.size > 15 * 1024 * 1024) {
            showNotification('❌ La imagen es muy grande. Máximo 15MB permitido.');
            clearImagePreview();
            return;
          }

          // Procesar imagen con compresión si es necesaria
          const reader = new FileReader();
          reader.onload = function(e) {
            const img = new Image();
            img.onload = function() {
              // Comprimir si es muy grande
              const canvas = document.createElement('canvas');
              const ctx = canvas.getContext('2d');

              let { width, height } = img;
              const maxSize = 1920;

              if (width > maxSize || height > maxSize) {
                if (width > height) {
                  height = (height * maxSize) / width;
                  width = maxSize;
                } else {
                  width = (width * maxSize) / height;
                  height = maxSize;
                }
              }

              canvas.width = width;
              canvas.height = height;
              ctx.drawImage(img, 0, 0, width, height);

              // Convertir a base64 con calidad optimizada
              const compressedDataUrl = canvas.toDataURL('image/jpeg', 0.85);

              if (imgPreview) imgPreview.src = compressedDataUrl;
              if (previewContainer) previewContainer.style.display = "flex";
              if (imgStatus) {
                const originalSize = (file.size / 1024).toFixed(1);
                const compressedSize = (compressedDataUrl.length * 0.75 / 1024).toFixed(1);
                imgStatus.textContent = `📎 Imagen procesada (${originalSize}KB → ${compressedSize}KB)`;
              }
              updateSendButton();
            };
            img.src = e.target.result;
          };

          reader.onerror = function() {
            showNotification('❌ Error al leer la imagen. Intenta con otra.');
            clearImagePreview();
          };

          reader.readAsDataURL(file);
        } else {
          clearImagePreview();
        }
      });
    }

    // Botón para quitar la miniatura
    if (clearPreviewBtn) {
      clearPreviewBtn.onclick = clearImagePreview;
    }

    // Actualizar el listener del input de texto
    if (preguntaInput) {
      preguntaInput.addEventListener('input', updateSendButton);
    }
  });
</script>
</body>
</html>
<script>
  // Sistema de fondos personalizados
  function initBackgroundSystem() {
    // Cargar fondo guardado
    const savedBg = localStorage.getItem('chatBackground');
    const savedBgType = localStorage.getItem('chatBackgroundType');

    if (savedBg && savedBgType) {
      if (savedBgType === 'animated') {
        applyAnimatedBackground(savedBg);
      } else if (savedBgType === 'custom') {
        applyCustomBackground(savedBg);
      }
    }

    setupBackgroundPanel();
  }

  function setupBackgroundPanel() {
    const backgroundSelector = document.getElementById('backgroundSelector');
    const backgroundPanel = document.getElementById('backgroundPanel');
    const closeBackgroundPanel = document.getElementById('closeBackgroundPanel');
    const uploadBgBtn = document.getElementById('uploadBgBtn');
    const customBgInput = document.getElementById('customBgInput');
    const bgOptions = document.querySelectorAll('.bg-option');
    const bgControls = document.getElementById('bgControls');

    // Abrir panel
    backgroundSelector?.addEventListener('click', () => {
      backgroundPanel.style.display = 'block';
    });

    // Cerrar panel
    closeBackgroundPanel?.addEventListener('click', () => {
      backgroundPanel.style.display = 'none';
    });

    // Fondos animados
    bgOptions.forEach(option => {
      option.addEventListener('click', () => {
        bgOptions.forEach(opt => opt.classList.remove('active'));
        option.classList.add('active');

        const bgType = option.dataset.bg;
        applyAnimatedBackground(bgType);
        localStorage.setItem('chatBackground', bgType);
        localStorage.setItem('chatBackgroundType', 'animated');

        if (bgType !== 'none') {
          bgControls.style.display = 'none';
        }
      });
    });

    // Subir imagen personalizada
    uploadBgBtn?.addEventListener('click', () => {
      customBgInput.click();
    });

    customBgInput?.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
          const imageData = e.target.result;
          applyCustomBackground(imageData);
          localStorage.setItem('chatBackground', imageData);
          localStorage.setItem('chatBackgroundType', 'custom');
          bgControls.style.display = 'block';

          // Limpiar selección de fondos animados
          bgOptions.forEach(opt => opt.classList.remove('active'));
        };
        reader.readAsDataURL(file);
      }
    });

    // Controles de imagen
    const bgOpacity = document.getElementById('bgOpacity');
    const bgBlur = document.getElementById('bgBlur');
    const bgPosition = document.getElementById('bgPosition');

    [bgOpacity, bgBlur, bgPosition].forEach(control => {
      control?.addEventListener('input', updateCustomBackground);
    });
  }

  function applyAnimatedBackground(type) {
    // Limpiar fondos anteriores
    document.body.className = document.body.className.replace(/bg-\w+/g, '');

    if (type !== 'none') {
      document.body.classList.add(`bg-${type}`);
    }

    // Limpiar imagen personalizada
    document.body.style.backgroundImage = '';
    const overlay = document.getElementById('bgOverlay');
    if (overlay) overlay.remove();
  }

  function applyCustomBackground(imageData) {
    // Limpiar fondos animados
    document.body.className = document.body.className.replace(/bg-\w+/g, '');

    const opacity = document.getElementById('bgOpacity')?.value || 20;
    const blur = document.getElementById('bgBlur')?.value || 2;
    const position = document.getElementById('bgPosition')?.value || 'cover';

    document.body.style.backgroundImage = `url(${imageData})`;
    document.body.style.backgroundSize = position;
    document.body.style.backgroundPosition = 'center';
    document.body.style.backgroundRepeat = position === 'repeat' ? 'repeat' : 'no-repeat';
    document.body.style.backgroundAttachment = 'fixed';

    // Aplicar overlay con opacidad y blur
    let overlay = document.getElementById('bgOverlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'bgOverlay';
      overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
      `;
      document.body.appendChild(overlay);
    }

    overlay.style.background = `rgba(0,0,0,${(100-opacity)/100})`;
    overlay.style.backdropFilter = `blur(${blur}px)`;
  }

  function updateCustomBackground() {
    const savedBg = localStorage.getItem('chatBackground');
    const savedBgType = localStorage.getItem('chatBackgroundType');

    if (savedBg && savedBgType === 'custom') {
      applyCustomBackground(savedBg);
    }
  }
</script>
