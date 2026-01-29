// static/history.js

document.addEventListener('DOMContentLoaded', () => {
    fetchHistory();
});

async function fetchHistory() {
    const historyGrid = document.getElementById('history-grid');
    
    // Radium Loading Animation
    historyGrid.innerHTML = '<p style="color: var(--primary);"><i class="fa-solid fa-circle-notch fa-spin"></i> Accessing secure archives...</p>';

    try {
        const response = await fetch('/api/history');
        const data = await response.json();

        if (data.length === 0) {
            historyGrid.innerHTML = '<p style="color: var(--text-muted);"><i class="fa-solid fa-folder-open"></i> No analysis logs found.</p>';
        } else {
            historyGrid.innerHTML = ""; // Clear Loading
            data.forEach(item => {
                const historyCard = document.createElement('div');
                historyCard.className = 'history-card';
                
                // Image path logic
                const imageSrc = `/static/${item.image_path}`;
                
                // Injected HTML with Icons and Radium Classes
                historyCard.innerHTML = `
                    <img src="${imageSrc}" alt="Scan Result">
                    <div class="history-card-content">
                        <small><i class="fa-regular fa-clock"></i> ${item.date}</small>
                        <hr style="border-color: #333; margin: 10px 0;">
                        <p>${item.analysis.substring(0, 120)}...</p>
                        <button class="delete-btn" onclick="deleteHistoryItem(${item.id}, this)">
                            <i class="fa-solid fa-trash-can"></i> Delete Log
                        </button>
                    </div>
                `;
                historyGrid.appendChild(historyCard);
            });
        }
    } catch (error) {
        console.error(error);
        historyGrid.innerHTML = `<p style="color: #ff4444;"><i class="fa-solid fa-triangle-exclamation"></i> Database connection failed.</p>`;
    }
}

async function deleteHistoryItem(id, buttonElement) {
    // Using a standard confirm, but you could make this a custom modal later
    if (!confirm("CONFIRM DELETION: This record will be permanently erased.")) {
        return;
    }

    // Visual feedback on button
    const originalText = buttonElement.innerHTML;
    buttonElement.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Erasing...';

    try {
        const response = await fetch(`/api/history/delete/${id}`, {
            method: 'DELETE',
        });

        const data = await response.json();

        if (data.success) {
            // Animate removal
            const card = buttonElement.closest('.history-card');
            card.style.opacity = '0';
            card.style.transform = 'scale(0.9)';
            setTimeout(() => card.remove(), 300); // Wait for animation
        } else {
            alert(`Error: ${data.message}`);
            buttonElement.innerHTML = originalText;
        }
    } catch (error) {
        alert("System Error: Could not delete record.");
        buttonElement.innerHTML = originalText;
    }
}