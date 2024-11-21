// Existing functions...

// Function to handle GPT button click
async function handleGptButtonClick() {
    abrirModal(); // Open modal when GPT button is clicked
    const tema = document.getElementById('tema')?.value.trim();
    if (!tema) {
        alert('Por favor, ingrese un tema.');
        return;
    }

    try {
        const response = await fetch('/api/generar-recurso', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tema: tema })
        });

        if (!response.ok) throw new Error('Error en la solicitud a la API');

        const data = await response.json();
        if (data.resource) {
            alert('Recurso generado con éxito: ' + data.resource.title);
            updateResourceList(data.resource);
        } else {
            alert('Error al generar recurso: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al generar recurso.');
    }
}

// Function to handle YouTube button click
async function handleYouTubeButtonClick() {
    abrirModal(); // Open modal when YouTube button is clicked
    const tema = document.getElementById('tema')?.value.trim();
    if (!tema) {
        alert('Por favor, ingrese un tema.');
        return;
    }

    try {
        const response = await fetch(`/api/youtube?query=${tema}`);
        if (!response.ok) throw new Error('Error en la solicitud a la API');

        const data = await response.json();
        data.items.forEach(item => {
            const resource = {
                title: item.snippet.title,
                description: item.snippet.description,
                link: `https://www.youtube.com/watch?v=${item.id.videoId}`,
                type: 'Video'
            };
            updateResourceList(resource);
        });
        alert('Recursos de YouTube generados con éxito.');
    } catch (error) {
        console.error('Error:', error);
        alert('Error al obtener recursos de YouTube.');
    }
}

// Function to handle Google Books button click
async function handleGoogleBooksButtonClick() {
    abrirModal(); // Open modal when Google Books button is clicked
    const tema = document.getElementById('tema')?.value.trim();
    if (!tema) {
        alert('Por favor, ingrese un tema.');
        return;
    }

    try {
        const response = await fetch(`/api/google-books?query=${tema}`);
        if (!response.ok) throw new Error('Error en la solicitud a la API');

        const data = await response.json();
        data.items.forEach(item => {
            const resource = {
                title: item.volumeInfo.title,
                description: item.volumeInfo.description || 'Sin descripción disponible.',
                link: item.volumeInfo.infoLink,
                type: 'Libro'
            };
            updateResourceList(resource);
        });
        alert('Recursos de Google Books generados con éxito.');
    } catch (error) {
        console.error('Error:', error);
        alert('Error al obtener recursos de Google Books.');
    }
}

// Function to update the resource list in the UI
function updateResourceList(resource) {
    const listaRecursos = document.querySelector('.resource-list');
    if (listaRecursos) {
        const nuevoRecurso = document.createElement('li');
        nuevoRecurso.innerHTML = `
            <h3>${resource.title}</h3>
            <p>${resource.description}</p>
            <a href="${resource.link}" target="_blank">Acceder al recurso</a>
        `;
        listaRecursos.appendChild(nuevoRecurso);
    }
}

// Ensure DOM is fully loaded before adding event listeners
document.addEventListener('DOMContentLoaded', function() {
    const gptButton = document.getElementById('gpt-btn');
    const youtubeButton = document.getElementById('youtube-btn');
    const googleBooksButton = document.getElementById('google-books-btn');

    console.log('gpt-btn:', gptButton);
    console.log('youtube-btn:', youtubeButton);
    console.log('google-books-btn:', googleBooksButton);

    if (gptButton) gptButton.addEventListener('click', handleGptButtonClick);
    if (youtubeButton) youtubeButton.addEventListener('click', handleYouTubeButtonClick);
    if (googleBooksButton) googleBooksButton.addEventListener('click', handleGoogleBooksButtonClick);
});

// Abrir y cerrar modal
const crearRecursoBtn = document.getElementById("crear-recurso-btn");
const recursoModal = document.getElementById("recurso-modal");
function abrirModal() { recursoModal.style.display = "block"; }
function cerrarModal() { recursoModal.style.display = "none"; }
crearRecursoBtn.onclick = abrirModal;

// Enviar el formulario para generar el recurso
document.getElementById("crear-recurso-form").onsubmit = async function(e) {
    e.preventDefault();
    const tema = document.getElementById("tema").value;

    try {
        const [gptResponse, educacionResponse, psicologiaResponse, youtubeResponse, booksResponse] = await Promise.all([
            fetch("/api/generar-recurso", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tema: tema })
            }),
            fetch("/api/generar-contenido-educacion", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ input: tema })
            }),
            fetch("/api/generar-contenido-psicologia", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ input: tema })
            }),
            fetch(`/api/youtube?query=${tema}`), // YouTube Data API
            fetch(`/api/google-books?query=${tema}`) // Google Books API
        ]);

        const [gptData, educacionData, psicologiaData, youtubeData, booksData] = await Promise.all([
            gptResponse.json(),
            educacionResponse.json(),
            psicologiaResponse.json(),
            youtubeResponse.json(),
            booksResponse.json()
        ]);

        if (gptResponse.ok && educacionResponse.ok && psicologiaResponse.ok && youtubeResponse.ok && booksResponse.ok) {
            alert("Recursos generados exitosamente.");

            let listaRecursos = document.querySelector(".resource-list");
            
            if (!listaRecursos) {
                listaRecursos = document.createElement("ul");
                listaRecursos.className = "resource-list";
                document.querySelector(".resource-section").appendChild(listaRecursos);
            }

            const recursosGenerados = [
                { title: gptData.resource.title, description: gptData.resource.description, link: gptData.resource.link },
                { title: "Contenido Educativo", description: educacionData.response, link: "#" },
                { title: "Contenido Psicológico", description: psicologiaData.response, link: "#" },
                ...youtubeData.items.map(item => ({
                    title: item.snippet.title,
                    description: item.snippet.description,
                    link: `https://www.youtube.com/watch?v=${item.id.videoId}`
                })),
                ...booksData.items.map(item => ({
                    title: item.volumeInfo.title,
                    description: item.volumeInfo.description || "Sin descripción disponible.",
                    link: item.volumeInfo.infoLink
                }))
            ];

            recursosGenerados.forEach(recurso => {
                const nuevoRecurso = document.createElement("li");
                nuevoRecurso.innerHTML = `
                    <h3>${recurso.title}</h3>
                    <p>${recurso.description}</p>
                    <a href="${recurso.link}" target="_blank">Acceder al recurso</a>
                `;
                listaRecursos.appendChild(nuevoRecurso);
            });

            cerrarModal();
        } else {
            alert("Hubo un error al generar los recursos.");
        }
    } catch (error) {
        alert("Hubo un error al generar los recursos.");
    }
};

// Handle API button clicks
document.getElementById("gpt-btn").onclick = async function() {
    const tema = document.getElementById("tema").value;
    const response = await fetch("/api/generar-recurso", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tema: tema })
    });
    const data = await response.json();
    if (response.ok) {
        alert("Recurso generado con éxito: " + data.resource.title);
    } else {
        alert("Error al generar recurso: " + data.error);
    }
};

document.getElementById("youtube-btn").onclick = async function() {
    const tema = document.getElementById("tema").value;
    const response = await fetch(`/api/youtube?query=${tema}`);
    const data = await response.json();
    if (response.ok) {
        data.items.forEach(item => {
            const nuevoRecurso = document.createElement("li");
            nuevoRecurso.innerHTML = `
                <h3>${item.snippet.title}</h3>
                <p>${item.snippet.description}</p>
                <a href="https://www.youtube.com/watch?v=${item.id.videoId}" target="_blank">Acceder al recurso</a>
            `;
            document.querySelector(".resource-list").appendChild(nuevoRecurso);
        });
        alert("Recursos de YouTube generados con éxito.");
    } else {
        alert("Error al obtener recursos de YouTube: " + data.error);
    }
};

document.getElementById("google-books-btn").onclick = async function() {
    const tema = document.getElementById("tema").value;
    const response = await fetch(`/api/google-books?query=${tema}`);
    const data = await response.json();
    if (response.ok) {
        data.items.forEach(item => {
            const nuevoRecurso = document.createElement("li");
            nuevoRecurso.innerHTML = `
                <h3>${item.volumeInfo.title}</h3>
                <p>${item.volumeInfo.description || "Sin descripción disponible."}</p>
                <a href="${item.volumeInfo.infoLink}" target="_blank">Acceder al recurso</a>
            `;
            document.querySelector(".resource-list").appendChild(nuevoRecurso);
        });
        alert("Recursos de Google Books generados con éxito.");
    } else {
        alert("Error al obtener recursos de Google Books: " + data.error);
    }
};

// Existing functions...
