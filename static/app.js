// static/app.js

// --- PAGE INITIALIZATION ---
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('login-form')) {
        setupLoginPage();
    }
    if (document.getElementById('analyze-form')) {
        setupAppPage();
    }
});

// --- LOGIN PAGE LOGIC ---
function setupLoginPage() {
    const loginForm = document.getElementById('login-form');
    const errorMessage = document.getElementById('error-message');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Prevent reload
        
        // Visual Feedback: Change button text
        const submitBtn = loginForm.querySelector('button');
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> AUTHENTICATING...';
        
        const formData = new FormData(loginForm);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });

            const result = await response.json();

            if (result.success) {
                window.location.href = '/app'; // Redirect to app page
            } else {
                errorMessage.textContent = "ACCESS DENIED: " + result.message;
                submitBtn.innerHTML = originalBtnText; // Reset button
            }
        } catch (error) {
            errorMessage.textContent = "CONNECTION ERROR";
            submitBtn.innerHTML = originalBtnText;
        }
    });
}

// --- MAIN APP PAGE LOGIC ---
function setupAppPage() {
    const analyzeForm = document.getElementById('analyze-form');
    const resultBox = document.getElementById('analysis-result');
    const fileInput = document.getElementById('file-upload');
    const imagePreview = document.getElementById('image-preview');

    // --- IMAGE PREVIEW FEATURE ---
    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
                // Cool "Ready" message
                resultBox.innerHTML = "<p style='color: var(--primary);'>Image loaded. System ready to scan.</p>";
            };
            reader.readAsDataURL(file);
        }
    });

    // --- IMAGE ANALYSIS HANDLER ---
    analyzeForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!fileInput.files || fileInput.files.length === 0) {
            resultBox.innerHTML = `<p style="color: #ff4444;">[ERROR] Please select an image file.</p>`;
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        // --- RADIUM LOADING ANIMATION ---
        resultBox.innerHTML = `
            <p><i class="fa-solid fa-circle-notch fa-spin"></i> CONNECTING TO NEURAL NETWORK...</p>
            <p>PROCESSING IMAGE DATA...</p>
        `;

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            // --- SMART ERROR HANDLING ---
            if (data.error && data.error.includes("blocked prompt")) {
                // Specific error for blocked medical images
                resultBox.innerHTML = `
                    <p style="color: #ff4444;">
                        <i class="fa-solid fa-ban"></i> <b>ANALYSIS BLOCKED</b>
                    </p>
                    <p>The AI safety filter flagged this image as sensitive medical content.</p>
                    <p><i>Try uploading a plant or object to test the system.</i></p>
                `;
            } else if (data.error) {
                // General error
                resultBox.innerHTML = `<p style="color: #ff4444;">[SYSTEM ERROR]: ${data.error}</p>`;
            } else {
                // --- SUCCESS ---
                let formattedAnalysis = data.analysis
    .replace(/\*/g, '<br>•')  // Replace asterisks with line break + bullet
    .replace(/\n/g, '<br>');  // Replace newlines with HTML breaks

resultBox.innerHTML = `
    <h3><i class="fa-solid fa-check-circle"></i> ANALYSIS COMPLETE</h3>
    <hr style="border-color: #333; margin: 15px 0;">
    <div style="line-height: 1.8;">
        ${formattedAnalysis}
    </div>
    <br><br>
    <p style="color: var(--primary-dim); font-size: 0.9em;">
        <i class="fa-solid fa-floppy-disk"></i> Data saved to <a href="/history">History Logs</a>.
    </p>
`;
                // Reset input but keep result visible
                fileInput.value = null;
                // Optional: Hide preview after success to clean up interface
                // imagePreview.style.display = 'none'; 
            }
        } catch (error) {
            console.error("Analysis fetch error:", error);
            resultBox.innerHTML = `<p style="color: #ff4444;">[NETWORK ERROR]: ${error.message}</p>`;
        }
    });
}