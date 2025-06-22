// Traducciones para el panel de ajustes
const translations = {
    es: {
        theme: "Tema",
        dark: "Oscuro",
        light: "Claro",
        color: "Color",
        font: "Fuente",
        lang: "Idioma",
        logout: "Cerrar sesión"
    },
    en: {
        theme: "Theme",
        dark: "Dark",
        light: "Light",
        color: "Color",
        font: "Font",
        lang: "Language",
        logout: "Log out"
    },
    fr: {
        theme: "Thème",
        dark: "Sombre",
        light: "Clair",
        color: "Couleur",
        font: "Police",
        lang: "Langue",
        logout: "Déconnexion"
    }
};

const socket = io();
let isAIResponding = false;

// Manejo de conexión del socket
socket.on('connect', () => {
    console.log('✅ Conectado al servidor');
    // Ocultar cualquier panel de error de conexión
    const errorPanel = document.querySelector('.connection-error, .error-panel, #errorPanel, #connectionError');
    if (errorPanel) {
        errorPanel.style.display = 'none';
    }
});

socket.on('disconnect', () => {
    console.log('❌ Desconectado del servidor');
    isAIResponding = false;
    isWaitingForResponse = false;
    updateSendButton();
    removeTypingIndicator();
});

socket.on('connect_error', (error) => {
    console.log('❌ Error de conexión:', error);
    isAIResponding = false;
    isWaitingForResponse = false;
    updateSendButton();
    removeTypingIndicator();
});
let currentTypingInterval = null;
let currentChatId = null;
let isWaitingForResponse = false;
let messageQueue = [];
const userEmail = window.USER_EMAIL || "default_user";
const WELCOME_MESSAGE = "¡Hola! Soy Alia, tu asistente de IA. ¿En qué puedo ayudarte hoy?";

// Variables globales para reconocimiento de voz
let recognition;
let recognizing = false;

// ---------- GUARDAR Y RESTAURAR ÚLTIMO CHAT ----------
function saveLastChatId(chatId) {
    if (chatId)
        localStorage.setItem("lastChatId_" + userEmail, chatId);
}
function getLastChatId() {
    return localStorage.getItem("lastChatId_" + userEmail) || null;
}
function deleteLastChatId() {
    localStorage.removeItem("lastChatId_" + userEmail);
}
// ------------------------------------------------------

document.addEventListener('DOMContentLoaded', function () {
    loadPreferences();
    setupEventListeners();
    loadChatHistory();
    
    // Forzar que el sidebar esté cerrado al inicio
    const sidebar = document.getElementById("sidebar");
    if (sidebar) {
        sidebar.classList.remove("show");
        sidebar.style.transform = "translateX(-100%)";
        sidebar.style.visibility = "hidden";
    }
    document.body.classList.remove("sidebar-open");
    
    // Timeout para asegurar que se mantenga cerrado
    setTimeout(() => {
        if (sidebar && !sidebar.classList.contains("show")) {
            sidebar.style.transform = "translateX(-100%)";
        }
    }, 100);
    
    // Limpiar estado inicial
    const previewContainer = document.getElementById("previewContainer");
    if (previewContainer) {
        previewContainer.style.display = 'none';
    }
    
    const imgInput = document.getElementById("imgInput");
    if (imgInput) {
        imgInput.value = '';
    }
    
    // Actualizar botón de envío al inicio
    updateSendButton();
    


    document.getElementById("emojiPicker").style.display = 'none';

    // Panel de selección de fuente (modal visual)
    const fontBtn = document.getElementById("fontSelectorBtn");
    const fontPanel = document.getElementById("fontPanel");
    const closeFontPanel = document.getElementById("closeFontPanel");
    const fontList = document.querySelectorAll(".font-list li");

    if (fontBtn && fontPanel) {
        fontBtn.onclick = function (e) {
            fontPanel.style.display = "block";
            // Marca la fuente actual
            const currentFont = localStorage.getItem("chatFont") || "'Roboto', sans-serif";
            fontList.forEach(li => {
                if (li.dataset.font === currentFont) {
                    li.classList.add("selected");
                } else {
                    li.classList.remove("selected");
                }
            });
        };

        // Cerrar
        closeFontPanel.onclick = function () {
            fontPanel.style.display = "none";
        };

        // Elegir fuente
        fontList.forEach(li => {
            li.onclick = function () {
                fontList.forEach(x => x.classList.remove("selected"));
                this.classList.add("selected");
                const value = this.dataset.font;
                document.body.style.fontFamily = value;
                document.body.style.setProperty("--font-family", value);
                localStorage.setItem("chatFont", value);
                fontBtn.textContent = this.textContent;
                fontPanel.style.display = "none";
            };
        });
    }

    // Cargar chats desde el servidor al iniciar con delay
    setTimeout(() => {
        fetch('/get_chats')
            .then(response => response.json())
            .then(data => {
                console.log('Chats cargados:', data);
                if (data.chats && data.chats.length > 0) {
                    const lastId = getLastChatId();
                    const exists = data.chats.some(c => c.id === lastId);
                    if (lastId && exists) {
                        loadChat(lastId);
                    } else {
                        loadChat(data.chats[0].id);
                    }
                } else {
                    document.getElementById("chatBox").innerHTML = `<div class="message ai"><div class="message-content">${WELCOME_MESSAGE}</div></div>`;
                    currentChatId = null;
                    deleteLastChatId();
                }
            })
            .catch(error => {
                console.error('Error cargando chats iniciales:', error);
                document.getElementById("chatBox").innerHTML = `<div class="message ai"><div class="message-content">${WELCOME_MESSAGE}</div></div>`;
                currentChatId = null;
                deleteLastChatId();
            });
    }, 500);

    document.getElementById("chatBox").addEventListener("scroll", function () {
        const btn = document.querySelector(".scroll-to-bottom-btn");
        if (this.scrollTop < this.scrollHeight - this.clientHeight - 10) {
            btn.style.opacity = 1;
            btn.style.pointerEvents = "auto";
        } else {
            btn.style.opacity = 0;
            btn.style.pointerEvents = "none";
        }
    });

    const scrollBtn = document.getElementById("scrollToBottomBtn");
    if (scrollBtn) {
        scrollBtn.addEventListener("click", function () {
            document.getElementById("chatBox").scrollTop = document.getElementById("chatBox").scrollHeight;
        });
    }

    // Variables globales para el modal de voz
    window.aliaVoiceModal = document.getElementById('aliaVoiceModal');
    window.aliaVoiceContent = document.getElementById('aliaVoiceContent');
    window.aliaVoiceText = document.getElementById('aliaVoiceText');
    window.speechSynthesis = window.speechSynthesis;

    // -------------------- RECONOCIMIENTO DE VOZ CON MODAL ALIA --------------------
    setupVoiceRecognition();

    addCopyButtonsToCodeBlocks();
});

function setupVoiceRecognition() {
    const micBtn = document.getElementById('micBtn');
    const preguntaInput = document.getElementById('pregunta');
    const aliaVoiceModal = document.getElementById('aliaVoiceModal');
    const aliaVoiceContent = document.getElementById('aliaVoiceContent');
    const aliaVoiceText = document.getElementById('aliaVoiceText');
    const aliaVoiceClose = document.getElementById('aliaVoiceClose');

    if (!micBtn || !preguntaInput || !aliaVoiceModal || !aliaVoiceText || !aliaVoiceContent || !aliaVoiceClose) {
        console.warn("Elementos de voz no encontrados");
        return;
    }

    function startRecognition() {
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
            aliaVoiceText.textContent = "Tu navegador no soporta reconocimiento de voz. Prueba con Chrome o Edge.";
            setTimeout(() => {
                aliaVoiceModal.style.display = 'none';
            }, 3000);
            return;
        }

        // Solicitar permisos de micrófono primero
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(() => {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                recognition = new SpeechRecognition();

                // Configuración mejorada
                recognition.lang = 'es-ES';
                recognition.continuous = false;
                recognition.interimResults = true; // Cambiar a true para resultados en tiempo real
                recognition.maxAlternatives = 1;

                // Configuraciones adicionales para mejor precisión
                if ('webkitSpeechRecognition' in window) {
                    recognition.continuous = false;
                    recognition.interimResults = true;
                }

                startRecognitionProcess();
            })
            .catch((error) => {
                console.error('Error solicitando permisos de micrófono:', error);
                let errorMsg = "Permisos de micrófono requeridos.";

                if (error.name === 'NotAllowedError') {
                    errorMsg = "Micrófono bloqueado. Permite el acceso y recarga la página.";
                } else if (error.name === 'NotFoundError') {
                    errorMsg = "No se detectó micrófono. Verifica tu dispositivo.";
                }

                aliaVoiceText.textContent = errorMsg;
                setTimeout(() => {
                    aliaVoiceModal.style.display = 'none';
                }, 4000);
            });
    }

    function startRecognitionProcess() {
        recognition.onstart = () => {
            recognizing = true;
            aliaVoiceContent.classList.remove('speaking');
            aliaVoiceContent.classList.add('listening');
            aliaVoiceText.textContent = "🎤 Escuchando... Habla ahora";
        };

        recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';

            // Procesar todos los resultados
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }

            // Mostrar transcripción en tiempo real
            if (interimTranscript) {
                aliaVoiceText.textContent = `🎤 Detectando: "${interimTranscript}"`;
            }

            // Cuando tengamos el resultado final
            if (finalTranscript) {
                const cleanedTranscript = finalTranscript.trim();
                if (cleanedTranscript.length > 0) {
                    document.getElementById('pregunta').value = cleanedTranscript;
                    document.getElementById('pregunta').dispatchEvent(new Event('input'));
                    updateSendButton();
                    aliaVoiceText.textContent = `✅ Recibido: "${cleanedTranscript}"`;
                    aliaVoiceContent.classList.remove('listening');
                    aliaVoiceContent.classList.add('speaking');

                    // Enviar automáticamente el mensaje con marcador de voz
                    setTimeout(() => {
                        sendVoiceMessage();
                    }, 1500);
                } else {
                    aliaVoiceText.textContent = "❌ No se detectó voz clara. Intenta de nuevo.";
                    setTimeout(() => {
                        aliaVoiceModal.style.display = 'none';
                    }, 3000);
                }
            }
        };

        recognition.onerror = (event) => {
            recognizing = false;
            console.log('Error de reconocimiento:', event.error);
            let errorMessage = "❌ No se pudo escuchar. Intenta de nuevo.";

            switch(event.error) {
                case 'no-speech':
                    errorMessage = "⚠️ No se detectó voz. Habla más cerca del micrófono.";
                    break;
                case 'audio-capture':
                    errorMessage = "❌ Error de micrófono. Verifica que esté funcionando.";
                    break;
                case 'not-allowed':
                    errorMessage = "🚫 Permiso de micrófono denegado. Permite el acceso.";
                    break;
                case 'network':
                    errorMessage = "📡 Error de conexión. Verifica tu internet.";
                    break;
                case 'service-not-allowed':
                    errorMessage = "❌ Servicio de voz no disponible.";
                    break;
                case 'aborted':
                    errorMessage = "⏹️ Reconocimiento cancelado.";
                    break;
                case 'language-not-supported':
                    errorMessage = "🌐 Idioma no soportado.";
                    break;
                default:
                    errorMessage = `❌ Error desconocido: ${event.error}`;
            }

            aliaVoiceText.textContent = errorMessage;
            aliaVoiceContent.classList.remove('listening', 'speaking');
            setTimeout(() => {
                aliaVoiceModal.style.display = 'none';
            }, 4000);
        };

        recognition.onend = () => {
            recognizing = false;
            if (aliaVoiceModal.style.display !== 'none' && !aliaVoiceContent.classList.contains('speaking')) {
                aliaVoiceText.textContent = "Finalizando...";
                setTimeout(() => {
                    aliaVoiceModal.style.display = 'none';
                }, 1000);
            }
        };

        recognition.start();
    }

    function stopRecognition() {
        if (recognition && recognizing) {
            recognition.stop();
            recognizing = false;
        }
    }

    function speakText(text) {
        if ('speechSynthesis' in window) {
            // Cancelar cualquier síntesis en curso
            window.speechSynthesis.cancel();

            // Limpiar el texto primero
            fetch('/text_to_speech', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.clean_text) {
                    const utterance = new SpeechSynthesisUtterance(data.clean_text);

                    // Configuración optimizada para español
                    utterance.lang = 'es-ES';
                    utterance.rate = 0.9; // Velocidad ajustada
                    utterance.pitch = 1.1; // Tono ligeramente más alto
                    utterance.volume = 1.0; // Volumen máximo

                    // Esperar a que las voces se carguen
                    const setVoiceAndSpeak = () => {
                        const voices = window.speechSynthesis.getVoices();
                        const spanishVoice = voices.find(voice => 
                            voice.lang.includes('es') && 
                            (voice.name.includes('Google') || voice.name.includes('Microsoft') || voice.name.includes('Español'))
                        ) || voices.find(voice => voice.lang.includes('es'));

                        if (spanishVoice) {
                            utterance.voice = spanishVoice;
                            console.log('Usando voz:', spanishVoice.name);
                        }

                        utterance.onstart = () => {
                            console.log('🔊 Iniciando síntesis de voz');
                            if (aliaVoiceModal && aliaVoiceModal.style.display === 'flex') {
                                aliaVoiceContent.classList.remove('listening');
                                aliaVoiceContent.classList.add('speaking');
                                aliaVoiceText.textContent = "🔊 Alia está hablando...";
                            }
                        };

                        utterance.onend = () => {
                            console.log('✅ Síntesis de voz completada');
                            if (aliaVoiceModal && aliaVoiceModal.style.display === 'flex') {
                                aliaVoiceContent.classList.remove('speaking');
                                aliaVoiceText.textContent = "✅ Conversación completada";
                                setTimeout(() => {
                                    aliaVoiceModal.style.display = 'none';
                                }, 1500);
                            }
                        };

                        utterance.onerror = (event) => {
                            console.error('❌ Error en síntesis de voz:', event.error);
                            if (aliaVoiceModal && aliaVoiceModal.style.display === 'flex') {
                                aliaVoiceText.textContent = "❌ Error reproduciendo audio";
                                setTimeout(() => {
                                    aliaVoiceModal.style.display = 'none';
                                }, 3000);
                            }
                        };

                        window.speechSynthesis.speak(utterance);
                    };

                    // Si las voces no están cargadas, esperar
                    if (window.speechSynthesis.getVoices().length === 0) {
                        window.speechSynthesis.onvoiceschanged = setVoiceAndSpeak;
                    } else {
                        setVoiceAndSpeak();
                    }

                } else {
                    console.error('Error preparando texto para voz:', data.error || 'Error desconocido');
                    // Fallback: usar el texto original limpio
                    const cleanText = text.replace(/<[^>]*>/g, '').substring(0, 300);
                    if (cleanText.trim()) {
                        const utterance = new SpeechSynthesisUtterance(cleanText);
                        utterance.lang = 'es-ES';
                        utterance.rate = 0.9;
                        utterance.pitch = 1.1;
                        window.speechSynthesis.speak(utterance);
                    }
                }
            })
            .catch(error => {
                console.error('Error en servicio de voz:', error);
                // Fallback: usar el texto original limpio
                const cleanText = text.replace(/<[^>]*>/g, '').substring(0, 300);
                if (cleanText.trim()) {
                    const utterance = new SpeechSynthesisUtterance(cleanText);
                    utterance.lang = 'es-ES';
                    utterance.rate = 0.9;
                    utterance.pitch = 1.1;
                    window.speechSynthesis.speak(utterance);
                }
            });
        } else {
            console.warn('⚠️ Síntesis de voz no disponible en este navegador');
            if (aliaVoiceModal && aliaVoiceModal.style.display === 'flex') {
                aliaVoiceText.textContent = "⚠️ Síntesis de voz no disponible en tu navegador";
                setTimeout(() => {
                    aliaVoiceModal.style.display = 'none';
                }, 3000);
            }
        }
    }

    // Función para enviar mensaje de voz
    function sendVoiceMessage() {
        const pregunta = document.getElementById("pregunta").value.trim();
        if (!pregunta) return;

        // Asegurar que tenemos un chat activo
        if (!currentChatId) {
            currentChatId = generateChatId();
            saveLastChatId(currentChatId);
        }

        // Mostrar mensaje del usuario
        addMessage(pregunta, 'user');

        // Limpiar input
        document.getElementById("pregunta").value = "";
        updateSendButton();

        // Mostrar indicador de escritura
        showTypingIndicator();

        // Marcar como respondiendo
        isAIResponding = true;
        isWaitingForResponse = true;

        // Enviar a través de SocketIO con marcador de voz
        const language = document.getElementById("lang-selector")?.value || "es";
        socket.emit("send_question", {
            pregunta: pregunta,
            chatId: currentChatId,
            language: language,
            isVoice: true,  // Marcador importante para voz
            hasImage: false
        });
    }

    micBtn.addEventListener('click', () => {
        console.log('🎤 Botón de micrófono presionado');
        if (aliaVoiceModal.style.display === 'flex') {
            console.log('🔇 Cerrando modal de voz');
            aliaVoiceModal.style.display = 'none';
            stopRecognition();
            window.speechSynthesis.cancel();
        } else {
            console.log('🎤 Abriendo modal de voz');
            aliaVoiceModal.style.display = 'flex';
            aliaVoiceText.textContent = "🎤 Preparando micrófono...";
            setTimeout(() => {
                startRecognition();
            }, 500);
        }
    });

    // Cerrar modal de voz
    aliaVoiceClose.addEventListener('click', () => {
        aliaVoiceModal.style.display = 'none';
        stopRecognition();
        window.speechSynthesis.cancel();
    });

    // Cerrar modal al hacer clic fuera
    aliaVoiceModal.addEventListener('click', (e) => {
        if (e.target === aliaVoiceModal) {
            aliaVoiceModal.style.display = 'none';
            stopRecognition();
            window.speechSynthesis.cancel();
        }
    });

    // Eventos SocketIO para voz
    socket.on("voice_status", function(data) {
        if (data.status === "speaking") {
            aliaVoiceContent.classList.remove('listening');
            aliaVoiceContent.classList.add('speaking');
            aliaVoiceText.textContent = "Alia está hablando...";
        } else if (data.status === "finished") {
            setTimeout(() => {
                aliaVoiceModal.style.display = 'none';
            }, 1000);
        }
    });

    socket.on("voice_response", function(data) {
        if (data.error) {
            console.error("Error de voz:", data.error);
            aliaVoiceText.textContent = "Error procesando voz";
        } else if (data.success) {
            console.log("Voz procesada:", data.text);
        }
    });
    
    // Escuchar actualizaciones de chat
    socket.on("chat_updated", function(data) {
        console.log("Chat actualizado:", data.chatId);
        loadChatHistory(); // Recargar historial cuando se actualiza un chat
    });

    // Función global para hablar respuestas de IA
    window.speakText = speakText;
}

function setupEventListeners() {
    // Sidebar
    document.getElementById("sidebarBtn").addEventListener("click", toggleSidebar);
    document.getElementById("closeSidebarBtn").addEventListener("click", toggleSidebar);

    // Emojis
    const emojiButton = document.getElementById("emojiButton");
    const emojiPicker = document.getElementById("emojiPicker");
    emojiButton.addEventListener("click", () => {
        emojiPicker.style.display = emojiPicker.style.display === 'block' ? 'none' : 'block';
    });

    emojiPicker.addEventListener('emoji-click', event => {
        const input = document.getElementById("pregunta");
        input.value += event.detail.unicode;
        input.focus();
        updateSendButton();
        emojiPicker.style.display = 'none';
    });

    document.addEventListener('click', (event) => {
        if (!emojiButton.contains(event.target) && !emojiPicker.contains(event.target)) {
            emojiPicker.style.display = 'none';
        }
    });

    // Configuración
    const settingsButton = document.getElementById("settingsButton");
    if (settingsButton) settingsButton.addEventListener("click", toggleSettings);

    // Formulario
    document.getElementById("chatForm").addEventListener("submit", function (e) {
        e.preventDefault();
        sendMessage();
    });

    document.getElementById("pregunta").addEventListener("input", updateSendButton);

    // Ajustes de tema, color, idioma
    document.querySelectorAll(".theme-btn").forEach(btn => btn.addEventListener("click", updateTheme));
    document.querySelectorAll(".color-btn").forEach(btn => btn.addEventListener("click", updateColor));
    const langSel = document.getElementById("lang-selector");
    if (langSel) langSel.addEventListener("change", updateLang);

    // Buscar chats
    document.getElementById("searchChatInput").addEventListener("input", function () {
        filterChats(this.value);
    });

    // Botón "Nuevo Chat"
    document.getElementById("newChatBtn").addEventListener("click", createNewChat);

    // Botón logout
    document.getElementById("btnLogout").addEventListener("click", () => {
        document.getElementById("confirmLogoutPanel").style.display = "flex";
    });
    document.getElementById("confirmLogoutNo").addEventListener("click", () => {
        document.getElementById("confirmLogoutPanel").style.display = "none";
    });
    document.getElementById("confirmLogoutYes").addEventListener("click", () => {
        window.location.href = "/logout";
    });
}

function toggleSettings(event) {
    event && event.stopPropagation && event.stopPropagation();
    const settings = document.querySelector(".settings-dropdown");
    if (settings.classList.contains("show")) {
        settings.classList.remove("show");
    } else {
        settings.classList.add("show");
        setTimeout(() => {
            function closeSettings(ev) {
                if (
                    !ev.target.closest(".settings-dropdown") &&
                    !ev.target.closest(".settings-btn")
                ) {
                    settings.classList.remove("show");
                    document.removeEventListener("click", closeSettings);
                }
            }
            document.addEventListener("click", closeSettings);
        });
    }
}

function createNewChat() {
    saveCurrentChat();

    // Detener cualquier respuesta activa
    if (isAIResponding) {
        if (socket && socket.connected) {
            socket.emit("stop_response");
        }
        removeTypingIndicator();
        if (currentTypingInterval) {
            clearInterval(currentTypingInterval);
            currentTypingInterval = null;
        }
    }

    currentChatId = Date.now().toString();
    saveLastChatId(currentChatId);

    document.getElementById("chatBox").innerHTML = '';
    addMessage(WELCOME_MESSAGE, 'ai');

    // Guardar mensaje de bienvenida en el servidor
    if (socket && socket.connected) {
        socket.emit("save_welcome_message", {
            chatId: currentChatId,
            message: WELCOME_MESSAGE
        });
    }

    // Actualizar historial inmediatamente
    setTimeout(() => {
        loadChatHistory();
    }, 100);

    toggleSidebar();

    isWaitingForResponse = false;
    isAIResponding = false;
    
    // Rehabilitar input
    const preguntaInput = document.getElementById("pregunta");
    preguntaInput.disabled = false;
    preguntaInput.placeholder = "Chatea con Alia...";
    
    updateSendButton();
}

function saveCurrentChat() {
    // Los mensajes ahora se guardan automáticamente en el servidor
    // Esta función ya no es necesaria pero se mantiene para compatibilidad
    return;
}

function loadChatHistory() {
    const chatList = document.getElementById("chatList");
    const newChatItem = chatList.querySelector(".new-chat-item");
    chatList.innerHTML = '';
    chatList.appendChild(newChatItem);

    console.log('Cargando historial de chats...');
    
    // Cargar chats desde el servidor
    fetch('/get_chats')
        .then(response => {
            console.log('Respuesta del servidor:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Datos recibidos:', data);
            if (data.chats && Array.isArray(data.chats)) {
                console.log(`Encontrados ${data.chats.length} chats`);
                data.chats.forEach(chat => {
                    console.log('Agregando chat:', chat.title);
                    const chatItem = document.createElement("li");
                    chatItem.className = "chat-item";
                    chatItem.innerHTML = `
                        <div class="chat-title">${chat.title}</div>
                        <div class="chat-actions">
                            <button class="delete-btn">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    `;
                    chatItem.addEventListener("click", () => loadChat(chat.id));
                    chatItem.querySelector(".delete-btn").addEventListener("click", (e) => {
                        e.stopPropagation();
                        deleteChat(chat.id);
                    });
                    chatList.insertBefore(chatItem, newChatItem);
                });
            } else {
                console.log('No se encontraron chats o formato incorrecto');
            }
        })
        .catch(error => {
            console.error('Error cargando historial:', error);
        });
}

function loadChat(chatId) {
    currentChatId = chatId;
    saveLastChatId(chatId);

    const chatBox = document.getElementById("chatBox");
    chatBox.innerHTML = '';

    // Cargar mensajes desde el servidor
    fetch(`/get_chat_messages/${chatId}`)
        .then(response => response.json())
        .then(data => {
            console.log(`Cargando mensajes para chat ${chatId}:`, data);
            if (data.messages && Array.isArray(data.messages)) {
                console.log(`Encontrados ${data.messages.length} mensajes`);
                data.messages.forEach(msg => {
                    console.log(`Agregando mensaje: ${msg.sender} - ${msg.content.substring(0, 50)}...`);
                    addMessage(msg.content, msg.sender, msg.time);
                });
            } else {
                console.log('No se encontraron mensajes o formato incorrecto');
            }
        })
        .catch(error => {
            console.error('Error cargando mensajes:', error);
        });

    toggleSidebar();
    scrollToBottom();

    isWaitingForResponse = false;
    isAIResponding = false;
    updateSendButton();
}

function deleteChat(chatId) {
    const confirmationPanel = document.getElementById("confirmationPanel");
    const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
    const cancelDeleteBtn = document.getElementById("cancelDeleteBtn");

    confirmationPanel.style.display = "flex";

    confirmDeleteBtn.onclick = () => {
        // Eliminar del servidor
        fetch(`/delete_chat/${chatId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadChatHistory();
                
                if (chatId === currentChatId) {
                    // Cargar el primer chat disponible o mostrar mensaje de bienvenida
                    fetch('/get_chats')
                        .then(response => response.json())
                        .then(data => {
                            if (data.chats && data.chats.length > 0) {
                                loadChat(data.chats[0].id);
                            } else {
                                document.getElementById("chatBox").innerHTML = `<div class="message ai"><div class="message-content">${WELCOME_MESSAGE}</div></div>`;
                                currentChatId = null;
                                deleteLastChatId();
                            }
                        });
                }
            }
        })
        .catch(error => {
            console.error('Error eliminando chat:', error);
        });
        
        confirmationPanel.style.display = "none";
    };

    cancelDeleteBtn.onclick = () => {
        confirmationPanel.style.display = "none";
    };
}

function generateChatId() {
    return Date.now().toString();
}

function generateImage() {
    const prompt = document.getElementById("pregunta").value.trim();
    if (!prompt) {
        showNotification("Escribe una descripción para buscar una imagen");
        return;
    }

    if (isAIResponding) {
        showNotification("Espera a que termine la respuesta actual");
        return;
    }

    if (!currentChatId) {
        showNotification("Debes crear un chat antes de generar imágenes");
        return;
    }

    // Mostrar mensaje del usuario
    addMessage(`🔍 Buscando imagen: "${prompt}"`, 'user');
    document.getElementById("pregunta").value = '';

    // Mostrar indicador de carga
    showTypingIndicator();

    fetch('/generate_image', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: prompt })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            removeTypingIndicator();
            if (data.error) {
                addMessage(`❌ Error: ${data.error}`, 'ai');
            } else {
                // Crear imagen con manejo de errores
                const imageMessage = `🎨 Imagen relacionada con "${prompt}":<br>
                <img src="${data.image_url}" 
                     alt="Imagen sobre ${prompt}" 
                     style="max-width: 100%; border-radius: 8px; margin-top: 10px; cursor: pointer; loading: lazy;" 
                     onclick="window.open('${data.image_url}', '_blank')"
                     onerror="this.style.display='none'; this.nextSibling.style.display='block';"
                     onload="this.nextSibling.style.display='none';">
                <div style="display: none; padding: 10px; background: #f0f0f0; border-radius: 8px; margin-top: 10px; text-align: center;">
                    ⚠️ No se pudo cargar la imagen. <a href="${data.image_url}" target="_blank">Intentar abrir en nueva pestaña</a>
                </div>`;
                addMessage(imageMessage, 'ai');
            }
        })
        .catch(error => {
            removeTypingIndicator();
            addMessage(`❌ Error de conexión: No se pudo conectar al servidor de imágenes. Intenta de nuevo en unos momentos.`, 'ai');
            console.error('Error generating image:', error);
        });
}

function sendMessage() {
    const preguntaInput = document.getElementById("pregunta");
    const pregunta = preguntaInput.value.trim();
    const imgInput = document.getElementById("imgInput");
    const hasImage = imgInput && imgInput.files && imgInput.files.length > 0;

    if (!pregunta && !hasImage) return;

    if (isAIResponding) {
        messageQueue.push({ text: pregunta, hasImage: hasImage });
        showNotification("Mensaje en cola. Se enviará cuando termine la respuesta actual.");
        preguntaInput.value = "";
        return;
    }

    if (!currentChatId) {
        currentChatId = generateChatId();
        saveLastChatId(currentChatId);
    }

    preguntaInput.disabled = true;
    preguntaInput.placeholder = "Espera a que Alia responda...";

    if (hasImage) {
        const file = imgInput.files[0];
        const reader = new FileReader();
        reader.onload = function(e) {
            const imageData = e.target.result;
            const messageText = pregunta || "🖼️ Imagen enviada para análisis";
            addMessage(messageText, 'user', null, imageData);

            if (socket && socket.connected) {
                socket.emit("send_question", {
                    pregunta: pregunta || 'Analiza esta imagen',
                    chatId: currentChatId,
                    language: document.getElementById("lang-selector")?.value || "es",
                    hasImage: true,
                    imageData: imageData,
                    forceImageMode: false
                });
            } else {
                showNotification("Error de conexión. Verifica tu internet.");
                preguntaInput.disabled = false;
                preguntaInput.placeholder = "Chatea con Alia...";
                isAIResponding = false;
                isWaitingForResponse = false;
                updateSendButton();
            }

            clearImagePreview();
        };
        reader.readAsDataURL(file);
    } else {
        addMessage(pregunta, 'user');
        if (socket && socket.connected) {
            socket.emit("send_question", {
                pregunta: pregunta,
                chatId: currentChatId,
                language: document.getElementById("lang-selector")?.value || "es",
                hasImage: false,
forceImageMode: false
            });
        } else {
            showNotification("Error de conexión. Verifica tu internet.");
            preguntaInput.disabled = false;
            preguntaInput.placeholder = "Chatea con Alia...";
            isAIResponding = false;
            isWaitingForResponse = false;
            updateSendButton();
        }
    }

    preguntaInput.value = "";
    isAIResponding = true;
    isWaitingForResponse = true;
    updateSendButton();
    showTypingIndicator();
}

function stopAIResponse() {
    if (isAIResponding) {
        if (socket && socket.connected) {
            socket.emit("stop_response");
        }
        removeTypingIndicator();

        if (currentTypingInterval) {
            clearInterval(currentTypingInterval);
            currentTypingInterval = null;
        }

        isAIResponding = false;
        isWaitingForResponse = false;
        updateSendButton();

        const preguntaInput = document.getElementById("pregunta");
        preguntaInput.disabled = false;
        preguntaInput.placeholder = "Chatea con Alia...";
    }
}

function updateSendButton() {
    const sendBtn = document.getElementById("sendButton");
    const hasText = document.getElementById("pregunta").value.trim().length > 0;
    const imgInput = document.getElementById("imgInput");
    const hasImage = imgInput && imgInput.files && imgInput.files.length > 0;
    const previewContainer = document.getElementById("previewContainer");
    const hasPreview = previewContainer && previewContainer.style.display === 'flex';

    if (isWaitingForResponse || isAIResponding) {
        sendBtn.innerHTML = '<i class="fas fa-stop"></i>';
        sendBtn.onclick = stopAIResponse;
        sendBtn.disabled = false;
        sendBtn.classList.add("stop-mode");
        sendBtn.classList.remove("active");
    } else if (hasText || hasImage || hasPreview) {
        sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        sendBtn.onclick = null;
        sendBtn.classList.remove("stop-mode");
        sendBtn.disabled = false;
        sendBtn.classList.add("active");
    } else {
        sendBtn.innerHTML = '<i class="fas fa-lock"></i>';
        sendBtn.onclick = null;
        sendBtn.classList.remove("stop-mode");
        sendBtn.disabled = true;
        sendBtn.classList.remove("active");
    }
}

socket.on("new_message", function (data) {
    isAIResponding = true;
    removeTypingIndicator();
    
    // Si es reemplazo de mensaje (para imágenes), reemplazar el último mensaje de IA
    if (data.replaceLastAI) {
        const chatBox = document.getElementById("chatBox");
        const messages = chatBox.querySelectorAll('.message.ai');
        if (messages.length > 0) {
            const lastAIMessage = messages[messages.length - 1];
            lastAIMessage.remove();
        }
    }
    
    const formattedResponse = formatAIResponse(data.message);
    typeMessageProgressive(formattedResponse, 'ai');

    // Verificar si es una respuesta a un mensaje de voz
    const isVoiceResponse = data.isVoiceResponse || 
                           (window.aliaVoiceModal && window.aliaVoiceModal.style.display === 'flex');

    if (isVoiceResponse) {
        // Usar el texto limpio del servidor si está disponible, sino limpiar localmente
        const textToSpeak = data.voiceText || data.message.replace(/<[^>]*>/g, '').replace(/\n+/g, ' ').trim();

        if (textToSpeak.length > 0) {
            // Esperar a que termine la animación de escritura antes de hablar
            setTimeout(() => {
                if (window.speakText && textToSpeak.length < 800) { // Límite de caracteres para voz
                    window.speakText(textToSpeak);
                } else if (textToSpeak.length >= 800) {
                    // Para textos muy largos, solo hablar un resumen
                    const summary = textToSpeak.substring(0, 200) + "... respuesta completa en pantalla.";
                    window.speakText && window.speakText(summary);
                }
            }, 1500);
        }
    }
});

function formatAIResponse(text) {
    // Procesar bloques de código primero
    text = text.replace(/```(\w+)?\n([\s\S]*?)```/g, function (match, language, code) {
        const lang = language || 'text';
        const escapedCode = code
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
        return `<pre class="terminal"><code class="language-${lang}">${escapedCode.trim()}</code></pre>`;
    });

    // Procesar código inline
    text = text.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

    // Procesar texto en negrita con asteriscos dobles **texto**
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Procesar texto en cursiva con asteriscos simples *texto*
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Dividir en párrafos después del procesamiento de código y markdown
    let paragraphs = text.split(/\n\s*\n/);

    paragraphs = paragraphs.map(para => {
        para = para.trim();
        if (!para) return '';

        // No procesar si ya es un bloque de código
        if (para.includes('<pre class="terminal">')) {
            return para;
        }

        // Resaltar palabras importantes
        para = para.replace(/\b(importante|clave|atención|nota|advertencia|warning|important|note)\b/gi, '<strong class="highlight">$1</strong>');

        // Procesar listas con guiones
        if (para.includes('\n- ') || para.startsWith('- ')) {
            const lines = para.split('\n');
            const listItems = [];
            let currentItem = '';

            for (let line of lines) {
                line = line.trim();
                if (line.startsWith('- ')) {
                    if (currentItem) {
                        listItems.push(`<li>${currentItem.trim()}</li>`);
                    }
                    currentItem = line.substring(2);
                } else if (line && currentItem) {
                    currentItem += ' ' + line;
                } else if (line && !currentItem) {
                    // Línea suelta que no es lista
                    if (listItems.length > 0) {
                        listItems.push(`</ul><p>${line}</p><ul>`);
                    } else {
                        return `<p>${line}</p>`;
                    }
                }
            }

            if (currentItem) {
                listItems.push(`<li>${currentItem.trim()}</li>`);
            }

            if (listItems.length > 0) {
                return `<ul>${listItems.join('')}</ul>`;
            }
        }

        // Procesar listas con asteriscos
        if (para.includes('\n* ') || para.startsWith('* ')) {
            const lines = para.split('\n');
            const listItems = [];
            let currentItem = '';

            for (let line of lines) {
                line = line.trim();
                if (line.startsWith('* ')) {
                    if (currentItem) {
                        listItems.push(`<li>${currentItem.trim()}</li>`);
                    }
                    currentItem = line.substring(2);
                } else if (line && currentItem) {
                    currentItem += ' ' + line;
                } else if (line && !currentItem) {
                    // Línea suelta que no es lista
                    if (listItems.length > 0) {
                        listItems.push(`</ul><p>${line}</p><ul>`);
                    } else {
                        return `<p>${line}</p>`;
                    }
                }
            }

            if (currentItem) {
                listItems.push(`<li>${currentItem.trim()}</li>`);
            }

            if (listItems.length > 0) {
                return `<ul>${listItems.join('')}</ul>`;
            }
        }

        // Procesar listas numeradas
        if (/^\d+\.\s/.test(para) || para.includes('\n1. ') || para.includes('\n2. ')) {
            const lines = para.split('\n');
            const listItems = [];
            let currentItem = '';

            for (let line of lines) {
                line = line.trim();
                if (/^\d+\.\s/.test(line)) {
                    if (currentItem) {
                        listItems.push(`<li>${currentItem.trim()}</li>`);
                    }
                    currentItem = line.replace(/^\d+\.\s/, '');
                } else if (line && currentItem) {
                    currentItem += ' ' + line;
                } else if (line && !currentItem) {
                    if (listItems.length > 0) {
                        listItems.push(`</ol><p>${line}</p><ol>`);
                    } else {
                        return `<p>${line}</p>`;
                    }
                }
            }

            if (currentItem) {
                listItems.push(`<li>${currentItem.trim()}</li>`);
            }

            if (listItems.length > 0) {
                return `<ol>${listItems.join('')}</ol>`;
            }
        }

        // Saltos de línea simples
        para = para.replace(/\n/g, '<br>');

        return `<p>${para}</p>`;
    });

    return `<div class="ai-response">${paragraphs.filter(p => p).join('')}</div>`;
}

function typeMessageProgressive(text, sender) {
    const chatBox = document.getElementById("chatBox");
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);
    const messageContent = document.createElement("div");
    messageContent.classList.add("message-content");
    messageDiv.appendChild(messageContent);
    const messageTime = document.createElement("div");
    messageTime.classList.add("message-time");
    messageDiv.appendChild(messageTime);
    const messageActions = document.createElement("div");
    messageActions.classList.add("message-actions");
    const copyBtn = document.createElement("button");
    copyBtn.classList.add("message-action");
    copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
    messageActions.appendChild(copyBtn);
    
    // Botón de regenerar solo para mensajes de IA
    if (sender === 'ai') {
        const regenBtn = document.createElement("button");
        regenBtn.classList.add("message-action", "regen-btn");
        regenBtn.innerHTML = '<i class="fas fa-redo"></i>';
        regenBtn.title = "Regenerar respuesta";
        regenBtn.addEventListener('click', () => regenerateResponse(messageDiv));
        messageActions.appendChild(regenBtn);
    }
    
    messageDiv.appendChild(messageActions);
    chatBox.appendChild(messageDiv);

    let i = 0;
    const speed = 10;
    let userScrolledUp = false;

    if (currentTypingInterval) {
        clearInterval(currentTypingInterval);
    }

    // Detectar si el usuario scrollea manualmente
    const onScroll = () => {
        const isAtBottom = chatBox.scrollTop >= chatBox.scrollHeight - chatBox.clientHeight - 50;
        userScrolledUp = !isAtBottom;
    };

    chatBox.addEventListener('scroll', onScroll);

    currentTypingInterval = setInterval(() => {
        if (i < text.length) {
            messageContent.innerHTML = text.substring(0, i + 1);
            i++;
            // Solo hacer scroll automático si el usuario no ha scrolleado hacia arriba
            if (!userScrolledUp) {
                scrollToBottom();
            }
        } else {
            clearInterval(currentTypingInterval);
            currentTypingInterval = null;
            chatBox.removeEventListener('scroll', onScroll);
            messageTime.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            copyBtn.addEventListener('click', () => copyMessage(text));
            isAIResponding = false;
            isWaitingForResponse = false;
            updateSendButton();
            processMessageQueue();
            saveCurrentChat();

            const preguntaInput = document.getElementById("pregunta");
            preguntaInput.disabled = false;
            preguntaInput.placeholder = "Chatea con Alia...";
            addCopyButtonsToCodeBlocks();

            // Scroll final solo si el usuario no scrolleó
            if (!userScrolledUp) {
                scrollToBottom();
            }
        }
    }, speed);
}

function processMessageQueue() {
    if (messageQueue.length > 0 && !isAIResponding) {
        const nextMessage = messageQueue.shift();
        document.getElementById("pregunta").value = nextMessage;
        sendMessage();
    }
}

function showTypingIndicator() {
    removeTypingIndicator(); // Eliminar cualquier indicador previo
    const chatBox = document.getElementById("chatBox");
    const typingDiv = document.createElement("div");
    typingDiv.classList.add("message", "ai");
    typingDiv.id = "typing-indicator";
    const typingContent = document.createElement("div");
    typingContent.classList.add("message-content", "typing-content");

    for (let i = 0; i < 3; i++) {
        const dot = document.createElement("span");
        dot.classList.add("typing-dot");
        typingContent.appendChild(dot);
    }

    typingDiv.appendChild(typingContent);
    chatBox.appendChild(typingDiv);
    scrollToBottom();
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById("typing-indicator");
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function updateSettingsPanelLang(lang) {
    const t = translations[lang] || translations.es;
    document.querySelector('.settings-section:nth-child(1) .settings-label').textContent = t.theme;
    document.querySelector('.theme-btn.dark').innerHTML = `<i class="fas fa-moon"></i> ${t.dark}`;
    document.querySelector('.theme-btn.light').innerHTML = `<i class="fas fa-sun"></i> ${t.light}`;
    document.querySelector('.settings-section:nth-child(2) .settings-label').textContent = t.color;
    document.querySelector('.settings-section:nth-child(3) .settings-label').textContent = t.font;
    document.querySelector('.settings-section:nth-child(4) .settings-label').textContent = t.lang;
    document.getElementById('btnLogout').innerHTML = `<i class="fas fa-sign-out-alt"></i> ${t.logout}`;
}

function loadPreferences() {
    const savedTheme = localStorage.getItem("chatTheme") || "dark";
    const savedColor = localStorage.getItem("chatColor") || "purple";
    const savedFont = localStorage.getItem("chatFont") || "'Poppins', sans-serif";
    const savedLang = localStorage.getItem("chatLang") || "es";

    document.body.classList.toggle("light-theme", savedTheme === "light");
    document.body.classList.toggle("dark-theme", savedTheme === "dark");

    document.querySelectorAll(".theme-btn").forEach(btn => {
        btn.classList.remove("active");
        if (btn.dataset.theme === savedTheme) btn.classList.add("active");
    });

    document.body.className = document.body.className.replace(/\b(purple|blue|green|red|orange|pink|teal)-theme\b/g, "");
    document.body.classList.add(`${savedColor}-theme`);
    document.querySelectorAll(".color-btn").forEach(btn => {
        btn.classList.remove("active");
        if (btn.dataset.color === savedColor) btn.classList.add("active");
    });

    document.body.style.fontFamily = savedFont;
    document.body.style.setProperty("--font-family", savedFont);

    // Poner nombre en el botón de fuente
    const fontSelBtn = document.getElementById("fontSelectorBtn");
    if (fontSelBtn) {
        const fontName = savedFont.replace(/['",]/g, '').split(',')[0].trim();
        fontSelBtn.textContent = fontName;
    }

    const langSel = document.getElementById("lang-selector");
    if (langSel) langSel.value = savedLang;

    updateSettingsPanelLang(savedLang);
}

function updateTheme() {
    const theme = this.dataset.theme;
    localStorage.setItem("chatTheme", theme);

    document.body.classList.toggle("light-theme", theme === "light");
    document.body.classList.toggle("dark-theme", theme === "dark");

    document.querySelectorAll(".theme-btn").forEach(btn => btn.classList.remove("active"));
    this.classList.add("active");
}

function updateColor() {
    const color = this.dataset.color;
    localStorage.setItem("chatColor", color);

    document.body.className = document.body.className.replace(/\b(purple|blue|green|red|orange|pink|teal)-theme\b/g, "");
    document.body.classList.add(`${color}-theme`);

    const savedTheme = localStorage.getItem("chatTheme") || "dark";
    document.body.classList.toggle("light-theme", savedTheme === "light");
    document.body.classList.toggle("dark-theme", savedTheme === "dark");

    document.querySelectorAll(".color-btn").forEach(btn => btn.classList.remove("active"));
    this.classList.add("active");
}

function updateLang() {
    const lang = this.value;
    localStorage.setItem("chatLang", lang);
    updateSettingsPanelLang(lang);
    showNotification((lang === "en") ? "Language changed." : (lang === "fr") ? "Langue changée." : "Idioma cambiado.");
}

function showNotification(message) {
    const notification = document.createElement("div");
    notification.className = "copy-notification";
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.remove();
    }, 2000);
}

function scrollToBottom() {
    const chatBox = document.getElementById("chatBox");
    chatBox.scrollTop = chatBox.scrollHeight;
}

function addMessage(text, sender, customTime, imageData) {
    const chatBox = document.getElementById("chatBox");
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);
    const messageContent = document.createElement("div");
    messageContent.classList.add("message-content");
    
    // Si hay imagen, mostrarla primero
    if (imageData && sender === 'user') {
        const imgElement = document.createElement("img");
        imgElement.src = imageData;
        imgElement.style.maxWidth = "250px";
        imgElement.style.maxHeight = "200px";
        imgElement.style.borderRadius = "12px";
        imgElement.style.marginBottom = "10px";
        imgElement.style.display = "block";
        imgElement.style.cursor = "pointer";
        imgElement.style.boxShadow = "0 2px 8px rgba(0,0,0,0.1)";
        imgElement.onclick = () => window.open(imageData, '_blank');
        messageContent.appendChild(imgElement);
    }
    
    // Agregar texto debajo de la imagen
    if (text && text.trim() !== "🖼️ Imagen enviada para análisis") {
        const textDiv = document.createElement("div");
        textDiv.innerHTML = text;
        messageContent.appendChild(textDiv);
    }
    
    const messageTime = document.createElement("div");
    messageTime.classList.add("message-time");
    messageTime.textContent = customTime || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const messageActions = document.createElement("div");
    messageActions.classList.add("message-actions");

    if (sender === 'user') {
        const editBtn = document.createElement("button");
        editBtn.classList.add("message-action");
        editBtn.innerHTML = '<i class="fas fa-edit"></i>';
        editBtn.addEventListener('click', () => editUserMessage(text));
        messageActions.appendChild(editBtn);
    }
    const copyBtn = document.createElement("button");
    copyBtn.classList.add("message-action");
    copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
    copyBtn.addEventListener('click', () => copyMessage(text));
    messageActions.appendChild(copyBtn);
    
    // Botón favorito para mensajes de IA
    if (sender === 'ai') {
        const favBtn = document.createElement("button");
        favBtn.classList.add("message-action", "fav-btn");
        favBtn.innerHTML = '<i class="far fa-star"></i>';
        favBtn.title = "Guardar como favorito";
        favBtn.addEventListener('click', () => toggleFavorite(messageDiv, text));
        messageActions.appendChild(favBtn);
    }
    
    // Botón favorito para mensajes de IA
    if (sender === 'ai') {
        const favBtn = document.createElement("button");
        favBtn.classList.add("message-action", "fav-btn");
        favBtn.innerHTML = '<i class="far fa-star"></i>';
        favBtn.title = "Guardar como favorito";
        favBtn.addEventListener('click', () => toggleFavorite(messageDiv, text));
        messageActions.appendChild(favBtn);
    }

    messageDiv.appendChild(messageContent);
    messageDiv.appendChild(messageTime);
    messageDiv.appendChild(messageActions);
    chatBox.appendChild(messageDiv);
    scrollToBottom();
    addCopyButtonsToCodeBlocks();
}

function editUserMessage(text) {
    const input = document.getElementById("pregunta");
    input.value = text.replace(/<[^>]*>/g, '');
    input.focus();
    updateSendButton();
}

function copyMessage(text) {
    const cleanText = text.replace(/<[^>]*>/g, '');
    navigator.clipboard.writeText(cleanText).then(() => {
        showNotification("Mensaje copiado");
    });
}

function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    sidebar.classList.toggle("show");
    document.body.classList.toggle("sidebar-open");
    document.getElementById("emojiPicker").style.display = 'none';
}

// Forzar cierre del sidebar al cargar
window.addEventListener('load', function() {
    const sidebar = document.getElementById("sidebar");
    if (sidebar) {
        sidebar.classList.remove("show");
        sidebar.style.transform = "translateX(-100%)";
        sidebar.style.visibility = "hidden";
    }
    document.body.classList.remove("sidebar-open");
});

// También al cambiar de página
window.addEventListener('beforeunload', function() {
    const sidebar = document.getElementById("sidebar");
    if (sidebar) {
        sidebar.classList.remove("show");
    }
});

function filterChats(query) {
    const list = document.getElementById("chatList");
    const items = list.getElementsByTagName("li");

    for (let i = 0; i < items.length; i++) {
        if (items[i].classList.contains("new-chat-item")) continue;
        let txtValue = items[i].textContent || items[i].innerText;
        items[i].style.display = txtValue.toLowerCase().includes(query.toLowerCase()) ? "" : "none";
    }
}

function regenerateResponse(messageDiv) {
    if (isAIResponding) {
        showNotification("Espera a que termine la respuesta actual");
        return;
    }

    // Encontrar el mensaje del usuario anterior
    let userMessage = null;
    let prevElement = messageDiv.previousElementSibling;
    
    while (prevElement) {
        if (prevElement.classList.contains('message') && prevElement.classList.contains('user')) {
            const messageContent = prevElement.querySelector('.message-content');
            if (messageContent) {
                userMessage = messageContent.textContent || messageContent.innerText;
                break;
            }
        }
        prevElement = prevElement.previousElementSibling;
    }

    if (!userMessage) {
        showNotification("No se pudo encontrar el mensaje original");
        return;
    }

    // Eliminar el mensaje de IA actual
    messageDiv.remove();

    // Reenviar la pregunta
    isAIResponding = true;
    isWaitingForResponse = true;
    updateSendButton();
    showTypingIndicator();

    if (socket && socket.connected) {
        socket.emit("send_question", {
            pregunta: userMessage,
            chatId: currentChatId,
            language: document.getElementById("lang-selector")?.value || "es",
            hasImage: false
        });
    } else {
        showNotification("Error de conexión. Verifica tu internet.");
        isAIResponding = false;
        isWaitingForResponse = false;
        updateSendButton();
        removeTypingIndicator();
    }
}

// Funciones para nuevas características
function saveToGallery(imageUrl, prompt) {
    showNotification("💾 Imagen guardada en galería");
    // La imagen ya se guarda automáticamente en el servidor
}

function shareImage(imageUrl) {
    if (navigator.share) {
        navigator.share({
            title: 'Imagen generada por Alia',
            url: imageUrl
        });
    } else {
        navigator.clipboard.writeText(imageUrl);
        showNotification("🔗 Enlace copiado al portapapeles");
    }
}

function toggleFavorite(messageDiv, text) {
    const favBtn = messageDiv.querySelector('.fav-btn');
    const isFavorite = favBtn.innerHTML.includes('fas');
    
    if (isFavorite) {
        favBtn.innerHTML = '<i class="far fa-star"></i>';
        removeFavorite(text);
        showNotification("⭐ Eliminado de favoritos");
    } else {
        favBtn.innerHTML = '<i class="fas fa-star"></i>';
        addFavorite(text);
        showNotification("⭐ Guardado en favoritos");
    }
}

function addFavorite(text) {
    let favorites = JSON.parse(localStorage.getItem('favorites_' + userEmail) || '[]');
    favorites.push({
        text: text,
        timestamp: new Date().toISOString()
    });
    localStorage.setItem('favorites_' + userEmail, JSON.stringify(favorites));
}

function removeFavorite(text) {
    let favorites = JSON.parse(localStorage.getItem('favorites_' + userEmail) || '[]');
    favorites = favorites.filter(fav => fav.text !== text);
    localStorage.setItem('favorites_' + userEmail, JSON.stringify(favorites));
}

// Funciones para nuevas características
function saveToGallery(imageUrl, prompt) {
    showNotification("💾 Imagen guardada en galería");
}

function shareImage(imageUrl) {
    if (navigator.share) {
        navigator.share({
            title: 'Imagen generada por Alia',
            url: imageUrl
        });
    } else {
        navigator.clipboard.writeText(imageUrl);
        showNotification("🔗 Enlace copiado al portapapeles");
    }
}

function downloadImage(imageUrl, filename) {
    // En app Android: descarga automática
    if (typeof Android !== 'undefined' && Android.downloadImage) {
        Android.downloadImage(imageUrl, filename.replace(/[^a-zA-Z0-9\s]/g, '_').substring(0, 20));
        showNotification("💾 Descargando imagen...");
        return;
    }
    
    // En navegador web: descarga directa
    fetch(imageUrl)
        .then(response => response.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `alia_${filename.replace(/[^a-zA-Z0-9\s]/g, '_')}.jpg`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            showNotification("💾 Imagen descargada");
        })
        .catch(() => {
            window.open(imageUrl, '_blank');
            showNotification("🔗 Imagen abierta. Mantén presionada para guardar");
        });
}

function openImageModal(imageUrl, title) {
    let modal = document.getElementById('imageModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'imageModal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            cursor: pointer;
        `;
        
        modal.innerHTML = `
            <div style="position: relative; max-width: 90%; max-height: 90%; text-align: center;">
                <img id="modalImage" style="max-width: 100%; max-height: 100%; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.5);" />
                <button id="closeModal" style="
                    position: absolute;
                    top: -15px;
                    right: -15px;
                    background: #ff4444;
                    color: white;
                    border: none;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    font-size: 20px;
                    cursor: pointer;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">×</button>
                <div style="margin-top: 15px;">
                    <button onclick="downloadImage('${imageUrl}', '${title}')" style="
                        background: #4caf50;
                        color: white;
                        border: none;
                        padding: 12px 20px;
                        border-radius: 25px;
                        margin: 0 10px;
                        cursor: pointer;
                        font-size: 16px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    ">💾 Descargar</button>
                    <button onclick="shareImage('${imageUrl}')" style="
                        background: #2196f3;
                        color: white;
                        border: none;
                        padding: 12px 20px;
                        border-radius: 25px;
                        margin: 0 10px;
                        cursor: pointer;
                        font-size: 16px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    ">🔗 Compartir</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal || e.target.id === 'closeModal') {
                closeImageModal();
            }
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.style.display === 'flex') {
                closeImageModal();
            }
        });
    }
    
    const modalImage = document.getElementById('modalImage');
    modalImage.src = imageUrl;
    modalImage.alt = title;
    modal.style.display = 'flex';
}

function closeImageModal() {
    const modal = document.getElementById('imageModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function regenerateImage(prompt) {
    // Cerrar modal si está abierto
    closeImageModal();
    
    // Poner el prompt en el input y enviarlo
    const input = document.getElementById('pregunta');
    input.value = `genera ${prompt}`;
    
    // Simular envío del formulario
    const form = document.getElementById('chatForm');
    if (form) {
        const event = new Event('submit', { bubbles: true, cancelable: true });
        form.dispatchEvent(event);
    }
    
    showNotification('🔄 Regenerando imagen...');
}

function toggleFavorite(messageDiv, text) {
    const favBtn = messageDiv.querySelector('.fav-btn');
    const isFavorite = favBtn.innerHTML.includes('fas');
    
    if (isFavorite) {
        favBtn.innerHTML = '<i class="far fa-star"></i>';
        removeFavorite(text);
        showNotification("⭐ Eliminado de favoritos");
    } else {
        favBtn.innerHTML = '<i class="fas fa-star"></i>';
        addFavorite(text);
        showNotification("⭐ Guardado en favoritos");
    }
}

function addFavorite(text) {
    let favorites = JSON.parse(localStorage.getItem('favorites_' + userEmail) || '[]');
    favorites.push({
        text: text,
        timestamp: new Date().toISOString()
    });
    localStorage.setItem('favorites_' + userEmail, JSON.stringify(favorites));
}

function removeFavorite(text) {
    let favorites = JSON.parse(localStorage.getItem('favorites_' + userEmail) || '[]');
    favorites = favorites.filter(fav => fav.text !== text);
    localStorage.setItem('favorites_' + userEmail, JSON.stringify(favorites));
}

function addCopyButtonsToCodeBlocks() {
    document.querySelectorAll('.message-content pre.terminal').forEach(function (pre) {
        if (!pre.classList.contains('code-block-terminal')) {
            pre.classList.add('code-block-terminal');
            
            let btn = document.createElement('button');
            btn.className = 'copy-code-btn';
            btn.type = 'button';
            btn.title = 'Copiar código completo';
            btn.innerHTML = '<i class="fas fa-copy"></i> Copiar';
            
            btn.onclick = function (e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Obtener el contenido preservando formato
                let textToCopy = '';
                
                // Crear un clon del elemento para manipularlo
                const preClone = pre.cloneNode(true);
                
                // Remover el botón de copiar del clon
                const copyBtn = preClone.querySelector('.copy-code-btn');
                if (copyBtn) {
                    copyBtn.remove();
                }
                
                // Obtener contenido completo
                textToCopy = preClone.innerText || preClone.textContent || '';
                
                if (!textToCopy.trim()) {
                    const codeElement = preClone.querySelector('code');
                    if (codeElement) {
                        textToCopy = codeElement.innerText || codeElement.textContent || '';
                    }
                }
                
                // Si innerText no preserva formato, usar textContent y agregar saltos manualmente
                if (textToCopy && !textToCopy.includes('\n')) {
                    // Usar textContent y procesar para agregar saltos de línea
                    const codeElement = preClone.querySelector('code') || preClone;
                    const walker = document.createTreeWalker(
                        codeElement,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    
                    let result = '';
                    let node;
                    while (node = walker.nextNode()) {
                        const parent = node.parentElement;
                        const text = node.textContent;
                        
                        // Agregar salto de línea después de ciertos elementos
                        if (parent && (parent.tagName === 'DIV' || parent.classList.contains('line'))) {
                            result += text + '\n';
                        } else {
                            result += text;
                        }
                    }
                    textToCopy = result;
                }
                
                // Limpiar y formatear
                textToCopy = textToCopy
                    .replace(/\u00a0/g, ' ')        // Espacios no separables
                    .replace(/\r\n/g, '\n')       // Normalizar saltos
                    .replace(/\r/g, '\n')
                    .replace(/\n{3,}/g, '\n\n')   // Máximo 2 saltos seguidos
                    .trim();
                
                console.log('=== DEBUG COPY ===');
                console.log('Longitud:', textToCopy.length);
                console.log('Primeras 5 líneas:');
                console.log(textToCopy.split('\n').slice(0, 5).join('\n'));
                console.log('================');
                
                if (textToCopy.length === 0) {
                    showNotification('❌ No se pudo obtener el código');
                    return;
                }
                
                if (navigator.clipboard && window.isSecureContext) {
                    navigator.clipboard.writeText(textToCopy).then(() => {
                        btn.classList.add('copied');
                        btn.innerHTML = '<i class="fas fa-check"></i> Copiado';
                        showNotification(`✅ Código completo copiado (${textToCopy.length} chars)`);
                        setTimeout(() => {
                            btn.classList.remove('copied');
                            btn.innerHTML = '<i class="fas fa-copy"></i> Copiar';
                        }, 2000);
                    }).catch(() => {
                        fallbackCopy(textToCopy, btn);
                    });
                } else {
                    fallbackCopy(textToCopy, btn);
                }
            };
            
            pre.appendChild(btn);
        }
    });
}

function fallbackCopy(text, btn) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        btn.classList.add('copied');
        btn.innerHTML = '<i class="fas fa-check"></i> Copiado';
        setTimeout(() => {
            btn.classList.remove('copied');
            btn.innerHTML = '<i class="fas fa-copy"></i> Copiar';
        }, 2000);
    } catch (err) {
        console.error('Error copiando:', err);
        btn.innerHTML = '<i class="fas fa-times"></i> Error';
        setTimeout(() => {
            btn.innerHTML = '<i class="fas fa-copy"></i> Copiar';
        }, 2000);
    }
    
    document.body.removeChild(textArea);
}

// Modal aviso historial local
function mostrarAvisoSiCorresponde() {
    if (!localStorage.getItem("historialAvisoNoMostrar")) {
        document.getElementById("historialAvisoModal").style.display = "flex";
    }
}

document.addEventListener('DOMContentLoaded', function () {
    // Esta variable debe estar definida por Jinja en el template:
    // const mostrarAvisoHistorial = true/false;
    if (typeof mostrarAvisoHistorial !== "undefined" && mostrarAvisoHistorial) {
        mostrarAvisoSiCorresponde();
    }

    const cerrarBtn = document.getElementById("cerrarAvisoBtn");
    if (cerrarBtn) {
        cerrarBtn.onclick = function () {
            if (document.getElementById("noMostrarAvisoCheck").checked) {
                localStorage.setItem("historialAvisoNoMostrar", "1");
            }
            document.getElementById("historialAvisoModal").style.display = "none";
        };
    }
});
