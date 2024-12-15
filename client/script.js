// script.js

document.addEventListener('DOMContentLoaded', function () {
    const cameraButton = document.getElementById('camera-button');
    const imageInput = document.getElementById('image-input');
    const preview = document.getElementById('preview');
    const form = document.getElementById('nutrition-form');

    // Capture from Camera
    cameraButton.addEventListener('click', () => {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                const video = document.createElement('video');
                video.srcObject = stream;
                video.autoplay = true;
                video.style.width = "100%";

                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');

                video.addEventListener('click', () => {
                    context.drawImage(video, 0, 0, canvas.width, canvas.height);
                    const imageDataUrl = canvas.toDataURL('image/png');
                    preview.src = imageDataUrl;
                    preview.style.display = 'block';

                    video.srcObject.getTracks().forEach(track => track.stop());
                });

                document.body.appendChild(video);
            })
            .catch(error => console.error("Camera access denied:", error));
    });

    // Handle Image Upload
    imageInput.addEventListener('change', () => {
        const file = imageInput.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = e => {
                preview.src = e.target.result;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    });

    // Submit Form
    form.addEventListener('submit', event => {
        event.preventDefault();
        const formData = new FormData(form);

        fetch('http://127.0.0.1:5000/analyze', {
            method: 'POST',
            body: formData,
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) displayResults(data);
                else displayError(data.error);
            })
            .catch(() => displayError("Failed to process your request. Try again."));
    });

    function displayResults(data) {
        const resultsContent = document.getElementById('results-content');
        resultsContent.innerHTML = `
            <p><strong>Gender:</strong> ${data.gender}</p>
            <p><strong>Extracted Text:</strong> ${data.extractedText}</p>
            <h3>Nutrition Data</h3>
            <ul>
                ${Object.entries(data.nutritionData).map(([key, value]) => `
                    <li>${key.replace(/_/g, ' ').toUpperCase()}: ${value}</li>
                `).join('')}
            </ul>
            <h3>RDV Analysis</h3>
            <ul>
                ${Object.entries(data.rdvAnalysis).map(([key, analysis]) => `
                    <li>${key.replace(/_/g, ' ').toUpperCase()}: ${analysis.percentage} (${analysis.status})</li>
                `).join('')}
            </ul>
            ${data.alerts.length ? `<h3>Alerts</h3><ul>${data.alerts.map(alert => `<li>${alert}</li>`).join('')}</ul>` : ''}
        `;
    }

    function displayError(message) {
        const resultsContent = document.getElementById('results-content');
        resultsContent.innerHTML = `<div class="alert error">${message}</div>`;
    }
});
