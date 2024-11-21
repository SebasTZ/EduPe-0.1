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
    document.getElementById('gpt-btn')?.addEventListener('click', handleGptButtonClick);
    document.getElementById('youtube-btn')?.addEventListener('click', handleYouTubeButtonClick);
    document.getElementById('google-books-btn')?.addEventListener('click', handleGoogleBooksButtonClick);
});

// Existing functions...
