// Función para enviar el mensaje en el chat
async function sendMessage() {
    const inputText = document.getElementById('input-text')?.value.trim();

    if (!inputText) {
        alert('Por favor, ingrese un mensaje.');
        return;
    }

    try {
        const chatBtn = document.getElementById('chat-btn');
        if (chatBtn) chatBtn.disabled = true;

        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) typingIndicator.style.display = 'block';

        const response = await fetch('/api/ia', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input: inputText })
        });

        if (!response.ok) throw new Error('Error en la solicitud a la API');

        const data = await response.json();
        const chatHistoryDiv = document.getElementById('chat-history');
        if (chatHistoryDiv) {
            const userMessage = `<div class="user-message"><strong>Usuario:</strong> ${inputText}</div>`;
            const botMessage = `<div class="bot-message"><strong>EduPe:</strong> ${data.response}</div>`;

            chatHistoryDiv.innerHTML += userMessage + botMessage;
            chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
        }

        document.getElementById('input-text').value = '';
        if (chatBtn) chatBtn.disabled = false;
        if (typingIndicator) typingIndicator.style.display = 'none';

    } catch (error) {
        console.error('Error:', error);
        alert('Ha ocurrido un error al enviar el mensaje.');
    }
}

// Función para cargar el historial del chat
async function loadChatHistory() {
    const chatHistoryDiv = document.getElementById('chat-history');

    if (!chatHistoryDiv) {
        console.error('Error: Element with ID chat-history not found.');
        return;
    }

    try {
        const response = await fetch('/api/chat-history', { method: 'GET' });
        if (!response.ok) throw new Error('Error al cargar el historial');

        const data = await response.json();
        data.history.forEach(chat => {
            const userMessage = `<div class="user-message"><strong>Usuario:</strong> ${chat.user_input}</div>`;
            const botMessage = `<div class="bot-message"><strong>EduPe:</strong> ${chat.ai_response}</div>`;
            chatHistoryDiv.innerHTML += userMessage + botMessage;
        });
    } catch (error) {
        console.error('Error al cargar historial:', error);
    }
}

// Función para generar contenido dinámico con manejo mejorado de errores
async function generarContenido(endpoint, inputFieldId, outputDivId) {
    const inputText = document.getElementById(inputFieldId)?.value.trim();

    if (!inputText) {
        alert('Por favor, ingrese un tema.');
        return;
    }

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input: inputText })
        });

        if (!response.ok) throw new Error('Error en la solicitud a la API');

        const data = await response.json();
        const outputDiv = document.getElementById(outputDivId);
        if (outputDiv) {
            outputDiv.innerHTML = `<p><strong>Contenido generado:</strong></p><p>${data.response}</p>`;
        } else {
            console.error('Elemento con ID no encontrado:', outputDivId);
        }

    } catch (error) {
        console.error('Error:', error);
        alert('Error al generar contenido. Inténtalo de nuevo más tarde.');
    }
}

// Función para generar preguntas automáticas en la página de evaluaciones
async function generarPreguntasEvaluacion() {
    const tema = document.getElementById('tema')?.value.trim();
    const generarBtn = document.getElementById('btn-generar-evaluacion');

    if (!tema) {
        alert('Por favor, ingrese un tema.');
        return;
    }

    if (generarBtn) {
        generarBtn.disabled = true;
    } else {
        console.error('Botón no encontrado: btn-generar-evaluacion');
        return;
    }

    try {
        const response = await fetch('/api/generar-evaluacion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tema: tema })
        });

        if (!response.ok) throw new Error('Error en la solicitud a la API');

        const data = await response.json();

        if (Array.isArray(data.response)) {
            const preguntasGeneradas = document.getElementById('preguntas-generadas');
            const preguntasContenido = document.getElementById('preguntas-contenido');

            if (preguntasGeneradas && preguntasContenido) {
                preguntasGeneradas.style.display = 'block';
                preguntasContenido.innerHTML = '';

                let preguntasHTML = '';
                data.response.forEach((preguntaObj, index) => {
                    preguntasHTML += `<div class="pregunta">
                        <p><strong>${preguntaObj.pregunta}</strong></p>`;
                    preguntaObj.opciones.forEach(opcion => {
                        preguntasHTML += `<label>
                            <input type="radio" name="pregunta-${index}" value="${opcion}">
                            ${opcion}
                        </label><br>`;
                    });
                    preguntasHTML += `</div>`;
                });

                preguntasContenido.innerHTML = preguntasHTML;
                const completarBtnDiv = document.createElement('div');
                completarBtnDiv.style.marginTop = '20px';
                completarBtnDiv.innerHTML = `<a href="/completar_evaluacion/${data.evaluacion_id}" class="btn btn-primary">Completar Evaluación</a>`;
                preguntasContenido.appendChild(completarBtnDiv);
            }
        } else {
            alert('Error al generar las preguntas. Formato de respuesta inesperado.');
        }

    } catch (error) {
        console.error('Error al generar preguntas:', error);
    } finally {
        if (generarBtn) generarBtn.disabled = false;
    }
}

// Función para enviar respuestas de la evaluación generada
async function enviarRespuestasEvaluacion() {
    const respuestas = {};
    document.querySelectorAll('input[type="radio"]:checked').forEach(input => {
        respuestas[input.name] = input.value;
    });

    try {
        const evaluacionId = window.evaluacionId;
        const response = await fetch(`/api/enviar-respuestas/${evaluacionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ respuestas: respuestas })
        });

        if (!response.ok) throw new Error('Error al enviar las respuestas');

        const data = await response.json();
        const preguntasContenidoDiv = document.getElementById('preguntas-contenido');

        // Mostrar resultados
        preguntasContenidoDiv.innerHTML = `<p>Correctas: ${data.correctas}/${data.total_preguntas} (${data.porcentaje}%)</p>
            <ul>${data.feedback.map(fb => `
                <li class="${fb.correcto ? 'correcto' : 'incorrecto'}">
                    <strong>${fb.pregunta}</strong>: ${fb.correcto ? 'Correcto' : 'Incorrecto'}
                    (Tu respuesta: ${fb.respuesta_usuario}, Correcta: ${fb.respuesta_correcta})
                </li>`).join('')}</ul>`;

        document.getElementById('resultados').style.display = 'block';
        document.getElementById('volver-evaluaciones').style.display = 'inline-block';
        document.getElementById('enviar-respuestas').style.display = 'none';

    } catch (error) {
        console.error('Error al enviar respuestas:', error);
    }
}

// JavaScript para manejar el clic en el botón "Volver a Evaluaciones y Guardar"
document.addEventListener('DOMContentLoaded', function () {
    // Obtener el ID de la evaluación
    const evaluacionId = document.getElementById('evaluacion-id').value;

    // Función para enviar respuestas de la evaluación
    async function enviarRespuestasEvaluacion() {
        const respuestas = {};
        document.querySelectorAll('input[type="radio"]:checked').forEach(input => {
            respuestas[input.name] = input.value;
        });

        try {
            const response = await fetch(`/api/enviar-respuestas/${evaluacionId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ respuestas: respuestas })
            });

            if (!response.ok) throw new Error('Error al enviar las respuestas');

            const data = await response.json();
            alert(`Resultados enviados. Correctas: ${data.correctas}/${data.total_preguntas} (${data.porcentaje}%)`);
        } catch (error) {
            console.error('Error al enviar respuestas:', error);
        }
    }

    // Función para almacenar resultados y redirigir a evaluaciones
    async function almacenarYVolverEvaluaciones() {
        const respuestas = {};
        document.querySelectorAll('input[type="radio"]:checked').forEach(input => {
            respuestas[input.name] = input.value;
        });

        try {
            // Almacenar las respuestas
            const response = await fetch(`/api/guardar-resultados-evaluacion`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    evaluacion_id: evaluacionId,
                    correctas: document.querySelectorAll('.correcto').length,
                    total: document.querySelectorAll('.pregunta').length,
                    nota: (document.querySelectorAll('.correcto').length / document.querySelectorAll('.pregunta').length) * 10,
                    comentarios: `Obtuviste ${document.querySelectorAll('.correcto').length} de ${document.querySelectorAll('.pregunta').length} preguntas correctas.`
                })
            });

            if (!response.ok) throw new Error('Error al guardar los resultados');

            const data = await response.json();
            console.log('Resultados almacenados:', data);
            window.location.href = '/evaluaciones'; // Redirigir a evaluaciones
        } catch (error) {
            console.error('Error al almacenar y volver a evaluaciones:', error);
        }
    }

    // Evento para el botón "Enviar Respuestas"
    const enviarBtn = document.getElementById('enviar-respuestas');
    if (enviarBtn) {
        enviarBtn.addEventListener('click', enviarRespuestasEvaluacion);
    }

    // Evento para el botón "Volver a Evaluaciones y Guardar"
    const volverBtn = document.getElementById('guardar-y-volver');
    if (volverBtn) {
        volverBtn.addEventListener('click', almacenarYVolverEvaluaciones);
    }
});

// Función para mostrar retroalimentación de la evaluación
async function mostrarRetroalimentacion(evaluacionId) {
    try {
        const response = await fetch(`/api/generar-retroalimentacion/${evaluacionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) throw new Error('Error al generar retroalimentación');

        const data = await response.json();
        if (data.retroalimentacion) {
            // Redirige a la página donde se muestra la retroalimentación
            window.location.href = `/evaluacion/feedback/${evaluacionId}`;
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Asociar funciones a botones y cargar el historial del chat
window.addEventListener('DOMContentLoaded', function() {
    document.getElementById('generar-evaluacion-form')?.addEventListener('submit', function(event) {
        event.preventDefault();
        generarPreguntasEvaluacion();
    });

    document.getElementById('form-preguntas-generadas')?.addEventListener('submit', function(event) {
        event.preventDefault();
        enviarRespuestasEvaluacion();
    });

    document.getElementById('chat-btn')?.addEventListener('click', function(event) {
        event.preventDefault();
        sendMessage();
    });

    document.getElementById('input-text')?.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            sendMessage();
        }
    });

    document.querySelectorAll('.suggestion-btn').forEach(button => {
        button.addEventListener('click', function() {
            document.getElementById('input-text').value = this.innerText;
            sendMessage();
        });
    });

    loadChatHistory();
});
