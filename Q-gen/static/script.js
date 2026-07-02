// Get references to all HTML elements we'll interact with
const generateBtn = document.getElementById('generateBtn');
const quoteText = document.getElementById('quoteText');
const quoteAuthor = document.getElementById('quoteAuthor');
const quoteTimestamp = document.getElementById('quoteTimestamp');
const historyList = document.getElementById('historyList');
const refreshHistoryBtn = document.getElementById('refreshHistoryBtn');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const saveBtn = document.getElementById('saveBtn');

// Store the current quote
let currentQuote = null;
async function generateQuote() {
    // Show loading state
    generateBtn.disabled = true;
    quoteLoader.classList.remove('hidden');
    quoteText.textContent = '';
    quoteAuthor.textContent = '';
    
    try {
        // Make API request to our backend
        const response = await fetch('/api/quotes/random');
        const data = await response.json();
        
        if (data.success) {
            // Update UI with new quote
            quoteText.textContent = data.quote;
            quoteAuthor.textContent = data.author;
            quoteTimestamp.textContent = `Viewed: ${data.viewed_at}`;
            
            // Store current quote
            currentQuote = data;
            saveBtn.disabled = false;
            
            // Refresh history
            await loadHistory();
        }
    } catch (error) {
        console.error('Error:', error);
        quoteText.textContent = 'Failed to load quote. Please try again.';
    } finally {
        generateBtn.disabled = false;
        quoteLoader.classList.add('hidden');
    }
}
async function loadHistory() {
    try {
        const response = await fetch('/api/quotes/history?limit=50');
        const data = await response.json();
        
        if (data.success) {
            renderHistory(data.history);
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

function renderHistory(quotes) {
    if (!quotes || quotes.length === 0) {
        historyList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox fa-3x"></i>
                <p>No quotes viewed yet.<br>Generate your first quote!</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    quotes.forEach(quote => {
        html += `
            <div class="history-item" data-id="${quote.id}">
                <div class="history-item-content">
                    <div class="history-item-text">"${escapeHtml(quote.quote_text)}"</div>
                    <div class="history-item-author">— ${escapeHtml(quote.author || 'Unknown')}</div>
                    <div class="history-item-time">${quote.viewed_at}</div>
                </div>
                <div class="history-item-actions">
                    <button class="btn-delete" onclick="deleteQuote(${quote.id})">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>
        `;
    });
    
    historyList.innerHTML = html;
}
async function deleteQuote(quoteId) {
    if (!confirm('Delete this quote from history?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/quotes/history/${quoteId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Remove item from DOM with animation
            const item = document.querySelector(`.history-item[data-id="${quoteId}"]`);
            if (item) {
                item.style.opacity = '0';
                item.style.transform = 'translateX(-20px)';
                setTimeout(() => item.remove(), 300);
            }
            showSuccess('Quote deleted!');
        }
    } catch (error) {
        console.error('Error deleting quote:', error);
        showError('Failed to delete quote.');
    }
}
async function clearHistory() {
    if (!confirm('Clear ALL history? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/quotes/history/clear', {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            renderHistory([]);
            showSuccess('History cleared!');
        }
    } catch (error) {
        console.error('Error clearing history:', error);
        showError('Failed to clear history.');
    }
}
function showSuccess(message) {
    showToast(message, 'success');
}

function showError(message) {
    showToast(message, 'error');
}

function showToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    const container = document.getElementById('toastContainer') || createToastContainer();
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        display: flex;
        flex-direction: column;
        gap: 10px;
        max-width: 350px;
    `;
    document.body.appendChild(container);
    return container;
}
// Set up event listeners
generateBtn.addEventListener('click', generateQuote);
refreshHistoryBtn.addEventListener('click', loadHistory);
clearHistoryBtn.addEventListener('click', clearHistory);
saveBtn.addEventListener('click', () => {
    showSuccess('Quote saved to history!');
    saveBtn.disabled = true;
    setTimeout(() => { saveBtn.disabled = false; }, 2000);
});

// Initialize app when page loads
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    generateQuote(); // Auto-generate first quote
});

// Keyboard shortcut: Space to generate
document.addEventListener('keydown', (e) => {
    if (e.key === ' ' && !e.repeat) {
        e.preventDefault();
        generateBtn.click();
    }
});