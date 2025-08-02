// LLM Bot Builder Dashboard JavaScript

// Global variables
let currentBotId = null;
let currentSessionId = 'default';
let currentClientId = null;
let apiKeyFieldCounter = 1;
let bots = [];
let clients = [];

// Initialize dashboard
async function loadDashboard() {
    showLoading(true);
    try {
        await Promise.all([fetchBots(), fetchClients()]);
        showSection('dashboard');
        renderBotList();
        renderClientList();
        loadClientOptions();
    } catch (error) {
        showNotification('Error loading dashboard: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Fetch all bots from API
async function fetchBots() {
    const response = await fetch('/api/bots');
    if (!response.ok) {
        throw new Error('Failed to fetch bots');
    }
    const data = await response.json();
    bots = data.bots || [];
}

// Render bot list in dashboard
function renderBotList() {
    const botList = document.getElementById('bot-list');
    const emptyState = document.getElementById('empty-state');
    
    if (bots.length === 0) {
        botList.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    botList.style.display = 'flex';
    
    botList.innerHTML = bots.map(bot => `
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card h-100">
                <div class="card-body">
                    <h5 class="card-title">${escapeHtml(bot.name)}</h5>
                    <p class="card-text text-muted">${escapeHtml(bot.description || 'No description')}</p>
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <small class="text-muted">
                            <i data-feather="book" class="feather-sm"></i>
                            ${bot.knowledge_count || 0} files
                        </small>
                        <small class="text-muted">
                            ${formatDate(bot.created_at)}
                        </small>
                    </div>
                </div>
                <div class="card-footer bg-transparent">
                    <div class="btn-group w-100">
                        <button class="btn btn-primary" onclick="viewBot(${bot.id})">
                            <i data-feather="eye"></i>
                            View
                        </button>
                        <button class="btn btn-outline-primary" onclick="testBot(${bot.id})">
                            <i data-feather="message-circle"></i>
                            Test
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    // Re-initialize Feather icons
    feather.replace();
}

// Show specific section
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Show target section
    const targetSection = document.getElementById(`${sectionName}-section`);
    if (targetSection) {
        targetSection.style.display = 'block';
    }
}

// Create bot form handler
document.getElementById('create-bot-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('bot-name').value,
        description: document.getElementById('bot-description').value,
        personality: document.getElementById('bot-personality').value,
        system_prompt: document.getElementById('system-prompt').value,
        temperature: parseFloat(document.getElementById('temperature').value),
        client_id: document.getElementById('client-select').value || null
    };
    
    try {
        showLoading(true);
        const response = await fetch('/api/bots', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to create bot');
        }
        
        const result = await response.json();
        showNotification('Bot created successfully!', 'success');
        
        // Reset form and reload dashboard
        document.getElementById('create-bot-form').reset();
        await loadDashboard();
        
    } catch (error) {
        showNotification('Error creating bot: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
});

// View bot details
async function viewBot(botId) {
    try {
        showLoading(true);
        currentBotId = botId;
        
        const response = await fetch(`/api/bots/${botId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch bot details');
        }
        
        const bot = await response.json();
        
        // Populate bot details
        document.getElementById('bot-detail-name').textContent = bot.name;
        document.getElementById('bot-detail-description').textContent = bot.description || 'No description';
        document.getElementById('bot-detail-personality').textContent = bot.personality || 'Default personality';
        document.getElementById('bot-detail-created').textContent = formatDate(bot.created_at);
        
        // Load knowledge bases
        await loadKnowledgeBases(botId);
        
        // Load deployments
        await loadDeployments(botId);
        
        // Clear chat
        document.getElementById('chat-messages').innerHTML = '';
        
        showSection('bot-detail');
        
    } catch (error) {
        showNotification('Error loading bot details: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Load knowledge bases
async function loadKnowledgeBases(botId) {
    try {
        const response = await fetch(`/api/bots/${botId}/knowledge`);
        if (!response.ok) {
            throw new Error('Failed to fetch knowledge bases');
        }
        
        const data = await response.json();
        const knowledgeBases = data.knowledge_bases || [];
        
        const knowledgeList = document.getElementById('knowledge-list');
        const noKnowledge = document.getElementById('no-knowledge');
        
        if (knowledgeBases.length === 0) {
            knowledgeList.style.display = 'none';
            noKnowledge.style.display = 'block';
            return;
        }
        
        noKnowledge.style.display = 'none';
        knowledgeList.style.display = 'block';
        
        knowledgeList.innerHTML = knowledgeBases.map(kb => `
            <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                <div>
                    <div class="fw-semibold">${escapeHtml(kb.filename)}</div>
                    <small class="text-muted">${kb.file_type.toUpperCase()} • ${formatDate(kb.upload_date)}</small>
                </div>
                <button class="btn btn-outline-danger btn-sm" onclick="deleteKnowledge(${kb.id})">
                    <i data-feather="trash"></i>
                </button>
            </div>
        `).join('');
        
        feather.replace();
        
    } catch (error) {
        console.error('Error loading knowledge bases:', error);
        showNotification('Error loading knowledge bases: ' + error.message, 'error');
    }
}

// Upload knowledge base
async function uploadKnowledge() {
    const fileInput = document.getElementById('knowledge-file');
    const file = fileInput.files[0];
    
    if (!file) {
        showNotification('Please select a file', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showLoading(true);
        const response = await fetch(`/api/bots/${currentBotId}/knowledge`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Failed to upload knowledge base');
        }
        
        const result = await response.json();
        showNotification('Knowledge base uploaded successfully!', 'success');
        
        // Close modal and reload bot details
        bootstrap.Modal.getInstance(document.getElementById('uploadModal')).hide();
        fileInput.value = '';
        await viewBot(currentBotId);
        
    } catch (error) {
        showNotification('Error uploading file: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Delete knowledge base
async function deleteKnowledge(knowledgeId) {
    if (!confirm('Are you sure you want to delete this knowledge base?')) {
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetch(`/api/bots/${currentBotId}/knowledge/${knowledgeId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete knowledge base');
        }
        
        showNotification('Knowledge base deleted successfully!', 'success');
        await viewBot(currentBotId);
        
    } catch (error) {
        showNotification('Error deleting knowledge base: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Load deployments
async function loadDeployments(botId) {
    try {
        const response = await fetch(`/api/bots/${botId}/deployments`);
        if (!response.ok) {
            throw new Error('Failed to fetch deployments');
        }
        
        const data = await response.json();
        const deployments = data.deployments || [];
        
        const deploymentList = document.getElementById('deployment-list');
        const noDeployments = document.getElementById('no-deployments');
        
        if (deployments.length === 0) {
            deploymentList.style.display = 'none';
            noDeployments.style.display = 'block';
            return;
        }
        
        noDeployments.style.display = 'none';
        deploymentList.style.display = 'block';
        
        deploymentList.innerHTML = deployments.map(deployment => `
            <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                <div>
                    <div class="fw-semibold">${deployment.platform.charAt(0).toUpperCase() + deployment.platform.slice(1)}</div>
                    <small class="text-muted">
                        <span class="badge bg-${getStatusColor(deployment.status)}">${deployment.status}</span>
                        • ${formatDate(deployment.created_at)}
                    </small>
                </div>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-secondary" onclick="viewDeployment('${deployment.deployment_id}')">
                        <i data-feather="eye"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="stopDeployment('${deployment.deployment_id}')">
                        <i data-feather="stop-circle"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        feather.replace();
        
    } catch (error) {
        console.error('Error loading deployments:', error);
    }
}

// Deploy bot
async function deployBot() {
    const platform = document.getElementById('platform-select').value;
    const configText = document.getElementById('deploy-config').value;
    
    if (!platform) {
        showNotification('Please select a platform', 'warning');
        return;
    }
    
    let config = {};
    if (configText.trim()) {
        try {
            config = JSON.parse(configText);
        } catch (error) {
            showNotification('Invalid JSON configuration', 'error');
            return;
        }
    }
    
    try {
        showLoading(true);
        const response = await fetch(`/api/bots/${currentBotId}/deploy`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                platform: platform,
                config: config
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to deploy bot');
        }
        
        const result = await response.json();
        showNotification(`Bot deployment to ${platform} initiated!`, 'success');
        
        // Close modal and reload deployments
        bootstrap.Modal.getInstance(document.getElementById('deployModal')).hide();
        document.getElementById('deploy-form').reset();
        await loadDeployments(currentBotId);
        
    } catch (error) {
        showNotification('Error deploying bot: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Chat functionality
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message || !currentBotId) {
        return;
    }
    
    // Add user message to chat
    addChatMessage('user', message);
    input.value = '';
    
    try {
        const response = await fetch(`/api/bots/${currentBotId}/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to send message');
        }
        
        const result = await response.json();
        addChatMessage('bot', result.response);
        
    } catch (error) {
        addChatMessage('bot', 'Sorry, I encountered an error. Please try again.');
        showNotification('Error sending message: ' + error.message, 'error');
    }
}

// Add message to chat
function addChatMessage(sender, message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message mb-2`;
    
    const isUser = sender === 'user';
    messageDiv.innerHTML = `
        <div class="p-2 rounded ${isUser ? 'bg-primary text-white ms-auto' : 'bg-light text-dark'}" 
             style="max-width: 80%; ${isUser ? 'margin-left: 20%;' : ''}">
            <div class="small mb-1 ${isUser ? 'text-white-50' : 'text-muted'}">
                ${isUser ? 'You' : 'Bot'}
            </div>
            <div>${escapeHtml(message)}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Handle Enter key in chat input
document.getElementById('chat-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendChatMessage();
    }
});

// Test bot (simplified chat)
async function testBot(botId) {
    currentBotId = botId;
    currentSessionId = 'test_' + Date.now();
    await viewBot(botId);
}

// Utility functions
function showLoading(show) {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        if (show) {
            spinner.classList.remove('d-none');
        } else {
            spinner.classList.add('d-none');
        }
    }
}

function showNotification(message, type = 'info') {
    const toast = document.getElementById('notification-toast');
    const toastBody = toast.querySelector('.toast-body');
    
    // Set message and styling based on type
    toastBody.textContent = message;
    toast.className = `toast show bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info'}`;
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function getStatusColor(status) {
    switch (status) {
        case 'active': return 'success';
        case 'pending': return 'warning';
        case 'failed': return 'danger';
        case 'stopped': return 'secondary';
        default: return 'secondary';
    }
}

// Placeholder functions for future implementation
function editBot() {
    showNotification('Edit functionality coming soon!', 'info');
}

function deleteBot() {
    if (confirm('Are you sure you want to delete this bot? This action cannot be undone.')) {
        showNotification('Delete functionality coming soon!', 'info');
    }
}

function viewDeployment(deploymentId) {
    showNotification('Deployment details coming soon!', 'info');
}

function stopDeployment(deploymentId) {
    if (confirm('Are you sure you want to stop this deployment?')) {
        showNotification('Stop deployment functionality coming soon!', 'info');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    feather.replace();
    loadDashboard();
});

// Legacy compatibility functions for backward compatibility with original starter code
async function createBot() {
    const res = await fetch('/api/bots', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: 'Test Bot', description: 'Legacy test bot'})
    });
    const data = await res.json();
    showNotification('Legacy bot created: ' + JSON.stringify(data), 'success');
}

async function sendMessage() {
    if (!currentBotId) {
        showNotification('Please select a bot first', 'warning');
        return;
    }
    
    const res = await fetch(`/api/bots/${currentBotId}/message`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: 'Hello AI!', session_id: 'legacy_session'})
    });
    const data = await res.json();
    document.getElementById('output').innerText = JSON.stringify(data, null, 2);
}

function viewDeployment(deploymentId) {
    showNotification('Deployment details coming soon!', 'info');
}

function stopDeployment(deploymentId) {
    if (confirm('Are you sure you want to stop this deployment?')) {
        showNotification('Stop deployment functionality coming soon!', 'info');
    }
}

// Legacy functions from starter code (for compatibility)
async function createBot() {
    const res = await fetch('/api/bots', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: 'Test Bot', description: 'Legacy test bot'})
    });
    const data = await res.json();
    showNotification('Legacy bot created: ' + JSON.stringify(data), 'success');
}

async function sendMessage() {
    if (!currentBotId) {
        showNotification('Please select a bot first', 'warning');
        return;
    }
    
    const res = await fetch(`/api/bots/${currentBotId}/message`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: 'Hello AI!'})
    });
    const data = await res.json();
    document.getElementById('output').innerText = JSON.stringify(data, null, 2);
}

// === CLIENT MANAGEMENT FUNCTIONS ===

// Fetch all clients from API
async function fetchClients() {
    try {
        const response = await fetch("/api/clients");
        if (!response.ok) {
            throw new Error("Failed to fetch clients");
        }
        const data = await response.json();
        clients = data.clients || [];
    } catch (error) {
        console.error("Error fetching clients:", error);
        clients = [];
    }
}

// Render client list
function renderClientList() {
    const clientList = document.getElementById("client-list");
    const noClients = document.getElementById("no-clients");
    
    if (clients.length === 0) {
        clientList.style.display = "none";
        noClients.style.display = "block";
        return;
    }
    
    noClients.style.display = "none";
    clientList.style.display = "block";
    
    clientList.innerHTML = clients.map(client => `
        <div class="d-flex justify-content-between align-items-center py-2 border-bottom client-item" 
             style="cursor: pointer;" onclick="selectClient(${client.id})">
            <div>
                <div class="fw-semibold">${escapeHtml(client.name)}</div>
                <small class="text-muted">${client.bot_count} bots</small>
            </div>
            <div class="btn-group">
                <button class="btn btn-outline-secondary btn-sm" onclick="editClientApiKeys(${client.id}); event.stopPropagation();">
                    <i data-feather="key"></i>
                </button>
                <button class="btn btn-outline-danger btn-sm" onclick="deleteClient(${client.id}); event.stopPropagation();">
                    <i data-feather="trash"></i>
                </button>
            </div>
        </div>
    `).join("");
    
    feather.replace();
}

// Load client options for bot creation
function loadClientOptions() {
    const clientSelect = document.getElementById("client-select");
    if (!clientSelect) return;
    
    clientSelect.innerHTML = "<option value=\"\">No specific client</option>" +
        clients.map(client => `<option value="${client.id}">${escapeHtml(client.name)}</option>`).join("");
}

// Show create client modal
function showCreateClientModal() {
    const modal = new bootstrap.Modal(document.getElementById("createClientModal"));
    document.getElementById("create-client-form").reset();
    document.getElementById("api-keys-container").innerHTML = `
        <div class="input-group mb-2">
            <input type="text" class="form-control" placeholder="Key name (e.g., telegram_token)" id="api-key-name-0">
            <input type="text" class="form-control" placeholder="Key value" id="api-key-value-0">
            <button class="btn btn-outline-danger" type="button" onclick="removeApiKeyField(0)">
                <i data-feather="x"></i>
            </button>
        </div>
    `;
    apiKeyFieldCounter = 1;
    feather.replace();
    modal.show();
}

// Create new client
async function createClient() {
    showLoading(true);
    try {
        const name = document.getElementById("client-name").value;
        const notes = document.getElementById("client-notes").value;
        
        const apiKeys = {};
        const container = document.getElementById("api-keys-container");
        const nameInputs = container.querySelectorAll("input[id^=\"api-key-name-\"]");
        
        nameInputs.forEach(nameInput => {
            const index = nameInput.id.split("-").pop();
            const valueInput = document.getElementById(`api-key-value-${index}`);
            
            if (nameInput.value.trim() && valueInput.value.trim()) {
                apiKeys[nameInput.value.trim()] = valueInput.value.trim();
            }
        });
        
        const response = await fetch("/api/clients", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: name,
                notes: notes,
                api_keys: apiKeys
            })
        });
        
        if (!response.ok) {
            throw new Error("Failed to create client");
        }
        
        showNotification("Client created successfully!", "success");
        bootstrap.Modal.getInstance(document.getElementById("createClientModal")).hide();
        await fetchClients();
        renderClientList();
        loadClientOptions();
        
    } catch (error) {
        showNotification("Error creating client: " + error.message, "error");
    } finally {
        showLoading(false);
    }
}

