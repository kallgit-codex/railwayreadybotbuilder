// Simple Dashboard JavaScript for LLM Bot Builder

// Global state
let clients = [];
let currentClient = null;
let currentBot = null;
let apiKeyCounter = 1;
let currentSessionId = null;

// Utility functions
function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
}

function showNotification(message, type = 'info') {
    const notifications = document.getElementById('notifications');
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    notifications.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Clear conversation functionality
async function clearConversation() {
    if (!currentBot) {
        showNotification('Please select a bot first', 'warning');
        return;
    }
    
    if (!confirm('Are you sure you want to clear the conversation? This will start a fresh session.')) {
        return;
    }
    
    showLoading(true);
    try {
        const response = await fetch(`/api/bots/${currentBot.id}/clear_conversation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId || 'default'
            })
        });
        
        if (!response.ok) throw new Error('Failed to clear conversation');
        
        const data = await response.json();
        
        // Clear the chat UI
        document.getElementById('chat-messages').innerHTML = '';
        
        // Start new session
        currentSessionId = data.new_session_id || generateSessionId();
        
        showNotification('Conversation cleared successfully! Starting fresh session.', 'success');
        
    } catch (error) {
        showNotification('Error clearing conversation: ' + error.message, 'error');
    } finally {
        showLoading(false);  
    }
}

// API functions
async function fetchClients() {
    try {
        const response = await fetch('/api/clients');
        if (!response.ok) throw new Error('Failed to fetch clients');
        const data = await response.json();
        clients = data.clients || [];
        renderClientsList();
    } catch (error) {
        console.error('Error fetching clients:', error);
        showNotification('Error loading clients: ' + error.message, 'error');
    }
}

async function fetchClientBots(clientId) {
    try {
        const response = await fetch(`/api/clients/${clientId}`);
        if (!response.ok) throw new Error('Failed to fetch client bots');
        const data = await response.json();
        return data.bots || [];
    } catch (error) {
        console.error('Error fetching client bots:', error);
        return [];
    }
}

async function fetchBotKnowledge(botId) {
    try {
        const response = await fetch(`/api/bots/${botId}/knowledge`);
        if (!response.ok) throw new Error('Failed to fetch bot knowledge');
        const data = await response.json();
        return data.knowledge_bases || [];
    } catch (error) {
        console.error('Error fetching bot knowledge:', error);
        return [];
    }
}

// Render functions
function renderClientsList() {
    const clientsList = document.getElementById('clients-list');
    const noClients = document.getElementById('no-clients');
    
    if (clients.length === 0) {
        noClients.style.display = 'block';
        clientsList.innerHTML = '';
        return;
    }
    
    noClients.style.display = 'none';
    clientsList.innerHTML = clients.map(client => `
        <div class="client-item p-2 mb-2 rounded ${currentClient && currentClient.id === client.id ? 'active' : ''}" 
             style="cursor: pointer;" onclick="selectClient(${client.id})">
            <div class="fw-semibold">${escapeHtml(client.name)}</div>
            <small class="text-muted">${client.bot_count || 0} bots</small>
        </div>
    `).join('');
}

async function renderBotsList(bots) {
    const botsList = document.getElementById('bots-list');
    const noBots = document.getElementById('no-bots');
    
    if (bots.length === 0) {
        noBots.style.display = 'block';
        botsList.innerHTML = '';
        return;
    }
    
    noBots.style.display = 'none';
    botsList.innerHTML = bots.map(bot => `
        <div class="col-md-6 mb-3">
            <div class="bot-item p-3">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="mb-0">${escapeHtml(bot.name)}</h6>
                    <div class="deployment-status-badges" data-bot-id="${bot.id}">
                        <span class="platform-status" data-platform="telegram" title="Telegram">
                            <i data-feather="message-circle" class="small-icon"></i>
                            <span class="status-indicator"></span>
                        </span>
                        <span class="platform-status" data-platform="whatsapp" title="WhatsApp">
                            <i data-feather="phone" class="small-icon"></i>
                            <span class="status-indicator"></span>
                        </span>
                        <span class="platform-status" data-platform="facebook" title="Facebook">
                            <i data-feather="facebook" class="small-icon"></i>
                            <span class="status-indicator"></span>
                        </span>
                        <span class="platform-status" data-platform="instagram" title="Instagram">
                            <i data-feather="instagram" class="small-icon"></i>
                            <span class="status-indicator"></span>
                        </span>
                    </div>
                </div>
                <p class="text-muted small mb-3">${escapeHtml(bot.description || 'No description')}</p>
                <div class="d-flex gap-2 flex-wrap">
                    <button class="btn btn-primary btn-sm" onclick="selectBot(${bot.id})">
                        <i data-feather="message-circle"></i> Chat
                    </button>
                    <button class="btn btn-outline-secondary btn-sm" onclick="selectBot(${bot.id})">
                        <i data-feather="upload"></i> Knowledge
                    </button>
                    <button class="btn btn-outline-info btn-sm" onclick="editBot(${bot.id})">
                        <i data-feather="settings"></i> Edit
                    </button>
                </div>
            </div>
        </div>
    `).join('');
    
    feather.replace();
    
    // Load deployment status for each bot
    bots.forEach(bot => loadBotDeploymentStatus(bot.id));
}

function renderKnowledgeFiles(knowledgeFiles) {
    const knowledgeList = document.getElementById('knowledge-list');
    const noKnowledge = document.getElementById('no-knowledge');
    
    if (knowledgeFiles.length === 0) {
        noKnowledge.style.display = 'block';
        knowledgeList.innerHTML = '';
        return;
    }
    
    noKnowledge.style.display = 'none';
    knowledgeList.innerHTML = knowledgeFiles.map(file => `
        <div class="knowledge-item p-2 mb-2">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <small class="fw-semibold">${escapeHtml(file.filename)}</small>
                    <br>
                    <small class="text-muted">${formatDate(file.created_at)}</small>
                </div>
                <button class="btn btn-outline-danger btn-sm" onclick="deleteKnowledge(${file.id})">
                    <i data-feather="trash-2"></i>
                </button>
            </div>
        </div>
    `).join('');
    
    feather.replace();
}

// Event handlers
async function selectClient(clientId) {
    showLoading(true);
    try {
        const client = clients.find(c => c.id === clientId);
        if (!client) return;
        
        currentClient = client;
        currentBot = null;
        
        // Update UI
        document.getElementById('welcome-message').style.display = 'none';
        document.getElementById('client-details').style.display = 'block';
        document.getElementById('bot-details').style.display = 'none';
        
        document.getElementById('client-name').textContent = client.name;
        document.getElementById('client-notes').textContent = client.notes || 'No notes';
        
        // Fetch and render bots
        const bots = await fetchClientBots(clientId);
        await renderBotsList(bots);
        renderClientsList(); // Re-render to update active state
        
        // Load client usage analytics and API keys
        loadClientUsage(clientId);
        loadClientApiKeys();
        
    } catch (error) {
        showNotification('Error selecting client: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function selectBot(botId) {
    showLoading(true);
    try {
        const response = await fetch(`/api/bots/${botId}`);
        if (!response.ok) throw new Error('Failed to fetch bot details');
        
        const bot = await response.json();
        currentBot = bot;
        
        // Show bot details section
        document.getElementById('bot-details').style.display = 'block';
        document.getElementById('bot-name').textContent = bot.name;
        document.getElementById('bot-description').textContent = bot.description || 'No description';
        
        // Load knowledge files
        const knowledgeFiles = await fetchBotKnowledge(botId);
        renderKnowledgeFiles(knowledgeFiles);
        
        // Clear chat and generate new session ID
        document.getElementById('chat-messages').innerHTML = '';
        currentSessionId = generateSessionId();
        
        // Load bot usage analytics
        loadBotUsage(botId);
        
    } catch (error) {
        showNotification('Error selecting bot: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Modal functions
function showCreateClientModal() {
    const modal = new bootstrap.Modal(document.getElementById('createClientModal'));
    document.getElementById('create-client-form').reset();
    document.getElementById('api-keys-container').innerHTML = `
        <div class="input-group mb-2">
            <input type="text" class="form-control" placeholder="Key name (e.g., telegram_token)" id="api-key-name-0">
            <input type="text" class="form-control" placeholder="Key value" id="api-key-value-0">
            <button class="btn btn-outline-danger" type="button" onclick="removeApiKeyField(0)">
                <i data-feather="x"></i>
            </button>
        </div>
    `;
    apiKeyCounter = 1;
    feather.replace();
    modal.show();
}

function showCreateBotModal() {
    if (!currentClient) {
        showNotification('Please select a client first', 'warning');
        return;
    }
    
    const modal = new bootstrap.Modal(document.getElementById('createBotModal'));
    document.getElementById('create-bot-form').reset();
    modal.show();
}

function addApiKeyField() {
    const container = document.getElementById('api-keys-container');
    const fieldHtml = `
        <div class="input-group mb-2">
            <input type="text" class="form-control editable-api-key-input" placeholder="Key name" id="api-key-name-${apiKeyCounter}" style="background-color: white; color: black;">
            <input type="password" class="form-control editable-api-key-input" placeholder="Key value" id="api-key-value-${apiKeyCounter}" style="background-color: white; color: black;">
            <button class="btn btn-outline-danger" type="button" onclick="removeApiKeyField(${apiKeyCounter})">
                <i data-feather="x"></i>
            </button>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', fieldHtml);
    apiKeyCounter++;
    feather.replace();
}

function removeApiKeyField(index) {
    const field = document.querySelector(`#api-key-name-${index}`).closest('.input-group');
    if (field) {
        field.remove();
    }
}

// Form handlers
document.getElementById('create-client-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    showLoading(true);
    
    try {
        const name = document.getElementById('new-client-name').value;
        const notes = document.getElementById('new-client-notes').value;
        
        // Collect API keys
        const apiKeys = {};
        const container = document.getElementById('api-keys-container');
        const nameInputs = container.querySelectorAll('input[id^="api-key-name-"]');
        
        nameInputs.forEach(nameInput => {
            const index = nameInput.id.split('-').pop();
            const valueInput = document.getElementById(`api-key-value-${index}`);
            
            if (nameInput.value.trim() && valueInput.value.trim()) {
                apiKeys[nameInput.value.trim()] = valueInput.value.trim();
            }
        });
        
        const response = await fetch('/api/clients', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                notes: notes,
                api_keys: apiKeys
            })
        });
        
        if (!response.ok) throw new Error('Failed to create client');
        
        showNotification('Client created successfully!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('createClientModal')).hide();
        await fetchClients();
        
    } catch (error) {
        showNotification('Error creating client: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
});

document.getElementById('create-bot-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    showLoading(true);
    
    try {
        const formData = {
            name: document.getElementById('new-bot-name').value,
            description: document.getElementById('new-bot-description').value,
            personality: document.getElementById('new-bot-personality').value,
            personality_description: document.getElementById('new-bot-personality-description').value,
            tone: document.getElementById('new-bot-tone').value,
            system_prompt: document.getElementById('new-bot-system-prompt').value,
            temperature: parseFloat(document.getElementById('new-bot-temperature').value),
            client_id: currentClient.id
        };
        
        const response = await fetch('/api/bots', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) throw new Error('Failed to create bot');
        
        showNotification('Bot created successfully!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('createBotModal')).hide();
        
        // Refresh current client view
        await selectClient(currentClient.id);
        
    } catch (error) {
        showNotification('Error creating bot: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
});

// Edit Bot form submission
document.getElementById('edit-bot-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    showLoading(true);
    
    try {
        const botId = document.getElementById('edit-bot-id').value;
        const formData = {
            name: document.getElementById('edit-bot-name').value,
            description: document.getElementById('edit-bot-description').value,
            personality: document.getElementById('edit-bot-personality').value,
            personality_description: document.getElementById('edit-bot-personality-description').value,
            tone: document.getElementById('edit-bot-tone').value,
            system_prompt: document.getElementById('edit-bot-system-prompt').value,
            temperature: parseFloat(document.getElementById('edit-bot-temperature').value),
            client_id: document.getElementById('edit-bot-client').value || null
        };
        
        const response = await fetch(`/api/bots/${botId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) throw new Error('Failed to update bot');
        
        showNotification('Bot updated successfully!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('editBotModal')).hide();
        
        // Refresh current client view to show updated bot
        if (currentClient) {
            await selectClient(currentClient.id);
        }
        
        // If this was the currently selected bot, refresh its details too
        if (currentBot && currentBot.id == botId) {
            await selectBot(botId);
        }
        
    } catch (error) {
        showNotification('Error updating bot: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
});

document.getElementById('upload-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    if (!currentBot) {
        showNotification('Please select a bot first', 'warning');
        return;
    }
    
    const fileInput = document.getElementById('knowledge-file');
    if (!fileInput.files[0]) {
        showNotification('Please select a file to upload', 'warning');
        return;
    }
    
    showLoading(true);
    
    try {
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        const response = await fetch(`/api/bots/${currentBot.id}/knowledge`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Failed to upload file');
        
        showNotification('File uploaded successfully!', 'success');
        fileInput.value = '';
        
        // Refresh knowledge files
        const knowledgeFiles = await fetchBotKnowledge(currentBot.id);
        renderKnowledgeFiles(knowledgeFiles);
        
    } catch (error) {
        showNotification('Error uploading file: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
});

document.getElementById('chat-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    if (!currentBot) {
        showNotification('Please select a bot first', 'warning');
        return;
    }
    
    const messageInput = document.getElementById('chat-input');
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addChatMessage(message, 'user');
    messageInput.value = '';
    
    try {
        const response = await fetch(`/api/bots/${currentBot.id}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId || generateSessionId()
            })
        });
        
        if (!response.ok) throw new Error('Failed to send message');
        
        const data = await response.json();
        addChatMessage(data.response, 'bot');
        
        // Update session ID if returned
        if (data.session_id && !currentSessionId) {
            currentSessionId = data.session_id;
        }
        
    } catch (error) {
        addChatMessage('Error: ' + error.message, 'bot');
        showNotification('Error sending message: ' + error.message, 'error');
    }
});

function addChatMessage(message, sender) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    messageDiv.textContent = message;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function deleteKnowledge(knowledgeId) {
    if (!confirm('Are you sure you want to delete this knowledge file?')) return;
    
    showLoading(true);
    try {
        const response = await fetch(`/api/knowledge/${knowledgeId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete knowledge file');
        
        showNotification('Knowledge file deleted successfully!', 'success');
        
        // Refresh knowledge files
        const knowledgeFiles = await fetchBotKnowledge(currentBot.id);
        renderKnowledgeFiles(knowledgeFiles);
        
    } catch (error) {
        showNotification('Error deleting knowledge file: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function editClientInfo() {
    showNotification('Client editing functionality coming soon!', 'info');
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
}

// === DEPLOYMENT FUNCTIONS ===

async function stopDeployment(deploymentId) {
    if (!confirm('Are you sure you want to delete this deployment? This will stop the bot on that platform.')) {
        return;
    }
    
    showLoading(true);
    try {
        const response = await fetch(`/api/deployments/${deploymentId}/stop`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to delete deployment');
        }
        
        const result = await response.json();
        showNotification(result.message || 'Deployment deleted successfully!', 'success');
        
        // Refresh the deployments list
        await loadDeployments();
        
    } catch (error) {
        console.error('Error deleting deployment:', error);
        showNotification('Error deleting deployment: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function cleanupDeployments() {
    if (!currentBot) {
        showNotification('No bot selected', 'error');
        return;
    }
    
    if (!confirm('This will remove duplicate deployments and keep only the latest one for each platform. Continue?')) {
        return;
    }
    
    showLoading(true);
    try {
        const response = await fetch(`/api/bots/${currentBot.id}/deployments/cleanup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to cleanup deployments');
        }
        
        const result = await response.json();
        showNotification(result.message || 'Deployments cleaned up successfully!', 'success');
        
        // Refresh the deployments list
        await loadDeployments();
        
    } catch (error) {
        console.error('Error cleaning up deployments:', error);
        showNotification('Error cleaning up deployments: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// === DEPLOYMENT WIZARD FUNCTIONS ===

function showDeployModal() {
    if (!currentBot) {
        alert('Please select a bot first');
        return;
    }
    
    // Load current client API keys
    loadClientApiKeysForDeployment();
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('deployBotModal'));
    modal.show();
}

async function loadClientApiKeysForDeployment() {
    try {
        if (!currentClient) return;
        
        const response = await fetch(`/api/clients/${currentClient.id}/api-keys`);
        const data = await response.json();
        
        const apiKeysDiv = document.getElementById('current-api-keys');
        const apiKeys = data.api_keys || {};
        
        if (Object.keys(apiKeys).length === 0) {
            apiKeysDiv.innerHTML = '<p class="text-muted mb-0">No API keys configured. Add them in client settings.</p>';
        } else {
            let html = '<div class="row">';
            for (const [key, value] of Object.entries(apiKeys)) {
                const maskedValue = value ? '*'.repeat(Math.min(value.length, 20)) : 'Not set';
                html += `
                    <div class="col-6 mb-2">
                        <small class="text-muted">${key}:</small><br>
                        <code class="small">${maskedValue}</code>
                    </div>
                `;
            }
            html += '</div>';
            apiKeysDiv.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading API keys:', error);
        document.getElementById('current-api-keys').innerHTML = '<p class="text-danger mb-0">Error loading API keys</p>';
    }
}

async function deployBot() {
    if (!currentBot) return;
    
    const platform = document.getElementById('deploy-platform').value;
    
    if (!platform) {
        alert('Please select a platform');
        return;
    }
    
    try {
        // Show deployment starting
        const deployButton = document.querySelector('#deployBotModal .btn-success');
        const originalText = deployButton ? deployButton.textContent : 'Deploy Bot';
        if (deployButton) {
            deployButton.textContent = 'Deploying...';
            deployButton.disabled = true;
        }
        
        const response = await fetch(`/api/bots/${currentBot.id}/deploy`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform })
        });
        
        const data = await response.json();
        console.log('Deployment response:', data);
        console.log('Response.ok:', response.ok);
        console.log('Data.success:', data.success);
        console.log('Full data structure:', Object.keys(data));
        
        if (response.ok && data.success) {
            // Close modal first
            bootstrap.Modal.getInstance(document.getElementById('deployBotModal')).hide();
            
            // Show detailed success message
            let message = `✅ Bot deployed successfully to ${platform.toUpperCase()}!`;
            if (data.webhook_url) {
                message += `\n\n🔗 Webhook URL: ${data.webhook_url}`;
            }
            if (data.webhook_status === 'registered') {
                message += '\n\n✅ Webhook automatically registered and ready to receive messages!';
            } else if (data.note) {
                message += `\n\n📝 Note: ${data.note}`;
            }
            
            alert(message);
            
            // Refresh deployments list
            loadDeployments();
            
            // Update deployment status indicators
            updateDeploymentStatusAfterDeploy(currentBot.id, platform, { success: true });
            
        } else {
            const errorMsg = data.error || 'Deployment failed';
            if (data.webhook_status === 'failed') {
                alert(`❌ Deployment failed: ${errorMsg}\n\nPlease check your API keys and try again.`);
            } else {
                alert(`❌ Deployment failed: ${errorMsg}`);
            }
        }
    } catch (error) {
        console.error('Error deploying bot:', error);
        alert(`❌ Error deploying bot: ${error.message}. Please try again.`);
    } finally {
        // Reset button
        const deployButton = document.querySelector('#deployBotModal .btn-success');
        if (deployButton) {
            deployButton.textContent = 'Deploy Bot';
            deployButton.disabled = false;
        }
    }
}

// Load deployment status for a specific bot
async function loadBotDeploymentStatus(botId) {
    try {
        const response = await fetch(`/api/bots/${botId}/status`);
        if (!response.ok) return;
        
        const data = await response.json();
        const deploymentStatus = data.deployment_status || {};
        
        // Update status indicators for this bot
        const badges = document.querySelector(`[data-bot-id="${botId}"]`);
        if (!badges) return;
        
        const platforms = ['telegram', 'whatsapp', 'facebook', 'instagram'];
        platforms.forEach(platform => {
            const platformStatus = badges.querySelector(`[data-platform="${platform}"]`);
            const indicator = platformStatus?.querySelector('.status-indicator');
            
            if (indicator) {
                const status = deploymentStatus[platform];
                if (status && status.deployed) {
                    indicator.className = 'status-indicator deployed';
                    indicator.title = `Deployed on ${new Date(status.last_deployed).toLocaleDateString()}`;
                } else {
                    indicator.className = 'status-indicator not-deployed';
                    indicator.title = 'Not deployed';
                }
            }
        });
    } catch (error) {
        console.error('Error loading deployment status for bot', botId, error);
    }
}

// Update deployment status after successful deployment
function updateDeploymentStatusAfterDeploy(botId, platform, status) {
    const badges = document.querySelector(`[data-bot-id="${botId}"]`);
    if (!badges) return;
    
    const platformStatus = badges.querySelector(`[data-platform="${platform}"]`);
    const indicator = platformStatus?.querySelector('.status-indicator');
    
    if (indicator) {
        if (status.success) {
            indicator.className = 'status-indicator deployed';
            indicator.title = `Deployed just now`;
        } else {
            indicator.className = 'status-indicator not-deployed';
            indicator.title = 'Deployment failed';
        }
    }
}

function showDeploymentInstructions(deployment) {
    const instructionsDiv = document.getElementById('deployment-instructions');
    const instructionsList = document.getElementById('instructions-list');
    
    let instructions = [];
    
    switch (deployment.platform) {
        case 'telegram':
            instructions = [
                'Create a bot with @BotFather on Telegram',
                `Set webhook URL: ${deployment.webhook_url}`,
                'Save the bot token in your client API keys',
                'Bot will now respond to messages automatically'
            ];
            break;
        case 'facebook_messenger':
            instructions = [
                'Create a Facebook App in Meta Developer Console',
                'Add Messenger product to your app',
                `Configure webhook URL: ${deployment.webhook_url}`,
                'Add page access token to client API keys',
                'Subscribe to page webhook events'
            ];
            break;
        case 'whatsapp':
            instructions = [
                'Set up WhatsApp Business API access',
                'Configure phone number and verify it',
                `Set webhook URL: ${deployment.webhook_url}`,
                'Add access token and phone number ID to client API keys'
            ];
            break;
        case 'instagram':
            instructions = [
                'Set up Instagram Business Account',
                'Create Facebook App with Instagram Basic Display',
                `Register webhook URL: ${deployment.webhook_url}`,
                'Add access token to client API keys'
            ];
            break;
    }
    
    instructionsList.innerHTML = instructions.map(inst => `<li>${inst}</li>`).join('');
    instructionsDiv.style.display = 'block';
}

async function loadDeployments() {
    if (!currentBot) return;
    
    try {
        const response = await fetch(`/api/bots/${currentBot.id}/deployments`);
        const data = await response.json();
        
        const deploymentsContainer = document.getElementById('deployments-container');
        const noDeployments = document.getElementById('no-deployments');
        
        if (!data.deployments || data.deployments.length === 0) {
            noDeployments.style.display = 'block';
            deploymentsContainer.innerHTML = '';
            return;
        }
        
        noDeployments.style.display = 'none';
        
        let html = '';
        data.deployments.forEach(deployment => {
            const statusColor = deployment.status === 'active' ? 'success' : 
                               deployment.status === 'failed' ? 'danger' : 'warning';
            
            html += `
                <div class="card mb-2">
                    <div class="card-body py-2">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${deployment.platform}</strong>
                                <span class="badge bg-${statusColor} ms-2">${deployment.status}</span>
                            </div>
                            <div>
                                <small class="text-muted">
                                    ${new Date(deployment.created_at).toLocaleDateString()}
                                </small>
                                <button class="btn btn-outline-danger btn-sm ms-2" 
                                        onclick="stopDeployment('${deployment.deployment_id}')">
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        deploymentsContainer.innerHTML = html;
    } catch (error) {
        console.error('Error loading deployments:', error);
    }
}

// Edit Bot functionality
async function editBot(botId) {
    showLoading(true);
    try {
        // Fetch bot details
        const response = await fetch(`/api/bots/${botId}`);
        if (!response.ok) throw new Error('Failed to fetch bot details');
        
        const bot = await response.json();
        
        // Populate the edit form
        document.getElementById('edit-bot-id').value = bot.id;
        document.getElementById('edit-bot-name').value = bot.name;
        document.getElementById('edit-bot-description').value = bot.description || '';
        document.getElementById('edit-bot-personality').value = bot.personality || 'helpful';
        document.getElementById('edit-bot-personality-description').value = bot.personality_description || '';
        document.getElementById('edit-bot-tone').value = bot.tone || 'conversational';
        document.getElementById('edit-bot-system-prompt').value = bot.system_prompt || '';
        document.getElementById('edit-bot-temperature').value = bot.temperature || 0.7;
        
        // Load clients for the dropdown
        await populateClientDropdown('edit-bot-client', bot.client_id);
        
        // Show the modal
        new bootstrap.Modal(document.getElementById('editBotModal')).show();
        
    } catch (error) {
        showNotification('Error loading bot details: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function populateClientDropdown(selectId, selectedClientId = null) {
    try {
        const response = await fetch('/api/clients');
        if (!response.ok) throw new Error('Failed to fetch clients');
        
        const clients = await response.json();
        const select = document.getElementById(selectId);
        
        // Clear existing options except first one
        select.innerHTML = '<option value="">No client (standalone bot)</option>';
        
        // Fix: clients data structure from API
        const clientsData = clients.clients || clients;
        clientsData.forEach(client => {
            const option = document.createElement('option');
            option.value = client.id;
            option.textContent = client.name;
            if (selectedClientId && client.id === selectedClientId) {
                option.selected = true;
            }
            select.appendChild(option);
        });
        
    } catch (error) {
        console.error('Error populating client dropdown:', error);
    }
}

async function stopDeployment(deploymentId) {
    if (!confirm('Are you sure you want to stop this deployment?')) return;
    
    try {
        const response = await fetch(`/api/deployments/${deploymentId}/stop`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Deployment stopped successfully');
            loadDeployments();
        } else {
            alert(`Error stopping deployment: ${data.error}`);
        }
    } catch (error) {
        console.error('Error stopping deployment:', error);
        alert('Error stopping deployment');
    }
}

// === USAGE ANALYTICS FUNCTIONS ===

async function loadClientUsage(clientId) {
    try {
        const response = await fetch(`/api/clients/${clientId}/usage?days=30`);
        const data = await response.json();
        
        if (response.ok) {
            displayClientUsageStats(data);
            displayClientTokenLimit(data.limit_status);
            displayBotBreakdown(data.bot_breakdown);
        } else {
            console.error('Error loading client usage:', data.error);
        }
    } catch (error) {
        console.error('Error loading client usage:', error);
    }
}

function displayClientUsageStats(data) {
    const statsContainer = document.getElementById('client-usage-stats');
    const stats = data.usage_stats;
    
    // Use new detailed fields with fallback to legacy fields
    const totalTokens = stats.total_tokens || 0;
    const inputTokens = stats.total_input_tokens || stats.total_prompt_tokens || 0;
    const outputTokens = stats.total_output_tokens || stats.total_completion_tokens || 0;
    const totalCost = stats.total_cost || stats.cost_estimate || 0;
    const inputCost = stats.total_input_cost || 0;
    const outputCost = stats.total_output_cost || 0;
    
    statsContainer.innerHTML = `
        <div class="col-3">
            <div class="text-center">
                <div class="h4 text-primary">${totalTokens.toLocaleString()}</div>
                <div class="small text-muted">Total Tokens</div>
                <div class="small text-secondary">In: ${inputTokens.toLocaleString()} | Out: ${outputTokens.toLocaleString()}</div>
            </div>
        </div>
        <div class="col-3">
            <div class="text-center">
                <div class="h4 text-success">${stats.total_messages.toLocaleString()}</div>
                <div class="small text-muted">Messages</div>
            </div>
        </div>
        <div class="col-3">
            <div class="text-center">
                <div class="h4 text-info">$${totalCost.toFixed(4)}</div>
                <div class="small text-muted">Total Cost</div>
                <div class="small text-secondary">In: $${inputCost.toFixed(4)} | Out: $${outputCost.toFixed(4)}</div>
            </div>
        </div>
        <div class="col-3">
            <div class="text-center">
                <div class="h4 text-warning">${Math.round(totalTokens / Math.max(stats.total_messages, 1))}</div>
                <div class="small text-muted">Avg Tokens/Msg</div>
            </div>
        </div>
    `;
}

function displayClientTokenLimit(limitStatus) {
    const limitDisplay = document.getElementById('token-limit-display');
    
    if (!limitStatus.has_limit) {
        limitDisplay.innerHTML = `
            <div class="text-muted">
                <i class="small">No token limit set</i>
            </div>
        `;
        return;
    }
    
    const { limit, current_usage, usage_percentage, is_over_limit, is_approaching_limit, warning_message } = limitStatus;
    
    let alertClass = 'alert-info';
    if (is_over_limit) {
        alertClass = 'alert-danger';
    } else if (is_approaching_limit) {
        alertClass = 'alert-warning';
    }
    
    limitDisplay.innerHTML = `
        <div class="alert ${alertClass} py-2 mb-0">
            <div class="d-flex justify-content-between">
                <div>
                    <strong>${current_usage.toLocaleString()} / ${limit.toLocaleString()}</strong> tokens used
                    <div class="small">${usage_percentage}% of monthly limit</div>
                </div>
                <div class="text-end">
                    <div class="small text-muted">Remaining: ${(limit - current_usage).toLocaleString()}</div>
                </div>
            </div>
            ${warning_message ? `<div class="small mt-1"><i class="text-muted">${warning_message}</i></div>` : ''}
        </div>
    `;
}

function displayBotBreakdown(breakdown) {
    const breakdownContainer = document.getElementById('bot-breakdown-list');
    
    if (!breakdown || breakdown.length === 0) {
        breakdownContainer.innerHTML = '<p class="text-muted small">No usage data available for this period.</p>';
        return;
    }
    
    let html = '';
    breakdown.forEach(bot => {
        // Use new detailed fields with fallback to legacy fields
        const totalTokens = bot.total_tokens || 0;
        const inputTokens = bot.total_input_tokens || bot.total_prompt_tokens || 0;
        const outputTokens = bot.total_output_tokens || bot.total_completion_tokens || 0;
        const totalCost = bot.total_cost || bot.cost_estimate || 0;
        
        html += `
            <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                <div>
                    <strong>${bot.bot_name}</strong>
                    <div class="small text-muted">${bot.total_messages} messages</div>
                    <div class="small text-secondary">In: ${inputTokens.toLocaleString()} | Out: ${outputTokens.toLocaleString()}</div>
                </div>
                <div class="text-end">
                    <div>${totalTokens.toLocaleString()} tokens</div>
                    <div class="small text-info">$${totalCost.toFixed(4)}</div>
                </div>
            </div>
        `;
    });
    
    breakdownContainer.innerHTML = html;
}

async function loadBotUsage(botId) {
    try {
        const response = await fetch(`/api/bots/${botId}/usage?days=30`);
        const data = await response.json();
        
        if (response.ok) {
            displayBotUsageStats(data);
            displayBotUsageChart(data.daily_usage);
        } else {
            console.error('Error loading bot usage:', data.error);
        }
    } catch (error) {
        console.error('Error loading bot usage:', error);
    }
}

function displayBotUsageStats(data) {
    const statsContainer = document.getElementById('bot-usage-stats');
    const stats = data.usage_stats;
    
    // Use new detailed fields with fallback to legacy fields
    const totalTokens = stats.total_tokens || 0;
    const inputTokens = stats.total_input_tokens || stats.total_prompt_tokens || 0;
    const outputTokens = stats.total_output_tokens || stats.total_completion_tokens || 0;
    const totalCost = stats.total_cost || stats.cost_estimate || 0;
    const inputCost = stats.total_input_cost || 0;
    const outputCost = stats.total_output_cost || 0;
    
    statsContainer.innerHTML = `
        <div class="col-3">
            <div class="text-center">
                <div class="h5 text-primary">${totalTokens.toLocaleString()}</div>
                <div class="small text-muted">Total Tokens</div>
                <div class="small text-secondary">In: ${inputTokens.toLocaleString()} | Out: ${outputTokens.toLocaleString()}</div>
            </div>
        </div>
        <div class="col-3">
            <div class="text-center">
                <div class="h5 text-success">${stats.total_messages.toLocaleString()}</div>
                <div class="small text-muted">Messages</div>
            </div>
        </div>
        <div class="col-3">
            <div class="text-center">
                <div class="h5 text-info">$${totalCost.toFixed(4)}</div>
                <div class="small text-muted">Total Cost</div>
                <div class="small text-secondary">In: $${inputCost.toFixed(4)} | Out: $${outputCost.toFixed(4)}</div>
            </div>
        </div>
        <div class="col-3">
            <div class="text-center">
                <div class="h5 text-warning">${Math.round(totalTokens / Math.max(stats.total_messages, 1))}</div>
                <div class="small text-muted">Avg Tokens/Msg</div>
            </div>
        </div>
    `;
}

function displayBotUsageChart(dailyUsage) {
    const chartContainer = document.getElementById('bot-usage-chart');
    
    if (!dailyUsage || dailyUsage.length === 0) {
        chartContainer.innerHTML = '<p class="text-muted small">No daily usage data available.</p>';
        return;
    }
    
    // Create a simple bar chart using CSS
    const maxTokens = Math.max(...dailyUsage.map(day => day.total_tokens));
    
    let html = '<div class="usage-chart">';
    dailyUsage.forEach(day => {
        const height = maxTokens > 0 ? (day.total_tokens / maxTokens) * 100 : 0;
        const date = new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        
        html += `
            <div class="chart-bar" style="position: relative; display: inline-block; width: 30px; margin: 0 2px; vertical-align: bottom;">
                <div style="background: var(--bs-primary); height: ${height}px; max-height: 100px; width: 100%; position: relative; top: ${100 - height}px;"
                     title="${date}: ${day.total_tokens} tokens, ${day.total_messages} messages"></div>
                <div style="font-size: 10px; text-align: center; margin-top: 5px; transform: rotate(-45deg); transform-origin: center;">${date}</div>
            </div>
        `;
    });
    html += '</div>';
    
    chartContainer.innerHTML = html;
}

async function editTokenLimit() {
    if (!currentClient) return;
    
    const currentLimit = currentClient.token_limit || '';
    const newLimit = prompt('Enter monthly token limit (leave empty for no limit):', currentLimit);
    
    if (newLimit === null) return; // User cancelled
    
    const limitValue = newLimit === '' ? null : parseInt(newLimit);
    
    if (newLimit !== '' && (isNaN(limitValue) || limitValue < 0)) {
        alert('Please enter a valid positive number or leave empty for no limit.');
        return;
    }
    
    try {
        const response = await fetch(`/api/clients/${currentClient.id}/token-limit`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token_limit: limitValue })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentClient.token_limit = limitValue;
            loadClientUsage(currentClient.id); // Refresh usage display
            showNotification('Token limit updated successfully!', 'success');
        } else {
            alert(`Error updating token limit: ${data.error}`);
        }
    } catch (error) {
        console.error('Error updating token limit:', error);
        alert('Error updating token limit');
    }
}

// Global conversation state (already defined above)

// === CONVERSATION MEMORY FUNCTIONS ===

async function loadConversationHistory() {
    if (!currentBot) return;
    
    try {
        const response = await fetch(`/api/bots/${currentBot.id}/conversations/${currentSessionId}`);
        if (response.ok) {
            const data = await response.json();
            displayConversationHistory(data.messages);
            updateConversationInfo(data.messages.length);
        }
    } catch (error) {
        console.error('Error loading conversation history:', error);
    }
}

// clearConversation function already defined above

async function autoFillWebhook() {
    const platformSelect = document.getElementById('deploy-platform');
    const webhookInput = document.getElementById('webhook-base-url');
    
    if (!platformSelect.value) {
        webhookInput.value = '';
        webhookInput.placeholder = 'Select a platform to auto-generate webhook URL';
        return;
    }
    
    try {
        // Map frontend platform values to backend expected values
        const platformMap = {
            'facebook_messenger': 'facebook',
            'telegram': 'telegram',
            'instagram': 'instagram',
            'whatsapp': 'whatsapp'
        };
        
        const backendPlatform = platformMap[platformSelect.value] || platformSelect.value;
        
        const response = await fetch(`/api/webhook-url/${backendPlatform}`);
        if (!response.ok) throw new Error('Failed to get webhook URL');
        
        const data = await response.json();
        webhookInput.value = data.webhook_url;
        webhookInput.removeAttribute('readonly');
        
    } catch (error) {
        console.error('Error auto-filling webhook:', error);
        webhookInput.value = '';
        webhookInput.placeholder = 'Error generating webhook URL - enter manually';
    }
}

function displayConversationHistory(messages) {
    const chatContainer = document.getElementById('chat-messages');
    chatContainer.innerHTML = '';
    
    messages.forEach(msg => {
        if (msg.role === 'user' || msg.role === 'assistant') {
            addMessageToChat(msg.content, msg.role === 'user' ? 'user' : 'bot');
        }
    });
    
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// === API KEYS MANAGEMENT ===

let editableApiKeyCounter = 0;
let originalApiKeys = {};

async function loadClientApiKeys() {
    if (!currentClient) return;
    
    try {
        const response = await fetch(`/api/clients/${currentClient.id}/api-keys`);
        const data = await response.json();
        const apiKeys = data.api_keys || {};
        
        displayApiKeys(apiKeys);
        originalApiKeys = { ...apiKeys };
        
    } catch (error) {
        console.error('Error loading API keys:', error);
        document.getElementById('api-keys-display').innerHTML = '<p class="text-danger">Error loading API keys</p>';
    }
}

function displayApiKeys(apiKeys) {
    const display = document.getElementById('api-keys-display');
    
    if (Object.keys(apiKeys).length === 0) {
        display.innerHTML = '<p class="text-muted">No API keys configured. Click "Edit Keys" to add some.</p>';
        return;
    }
    
    let html = '<div class="row">';
    for (const [key, value] of Object.entries(apiKeys)) {
        const maskedValue = value ? '•'.repeat(20) : 'Not set';
        html += `
            <div class="col-md-6 mb-3">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${escapeHtml(key)}</strong><br>
                        <small class="text-muted font-monospace">${maskedValue}</small>
                    </div>
                </div>
            </div>
        `;
    }
    html += '</div>';
    display.innerHTML = html;
}

function editApiKeys() {
    if (!currentClient) return;
    
    // Hide display, show editor
    document.getElementById('api-keys-display').style.display = 'none';
    document.getElementById('api-keys-editor').style.display = 'block';
    
    // Populate editor with current keys
    populateApiKeysEditor(originalApiKeys);
}

function populateApiKeysEditor(apiKeys) {
    const container = document.getElementById('editable-api-keys-container');
    container.innerHTML = '';
    editableApiKeyCounter = 0;
    
    // Add existing keys
    for (const [key, value] of Object.entries(apiKeys)) {
        addEditableApiKeyField(key, value);
    }
    
    // Add one empty field if no keys exist
    if (Object.keys(apiKeys).length === 0) {
        addEditableApiKeyField();
    }
    
    feather.replace();
}

function addEditableApiKeyField(keyName = '', keyValue = '') {
    const container = document.getElementById('editable-api-keys-container');
    const fieldHtml = `
        <div class="input-group mb-3" id="editable-key-${editableApiKeyCounter}">
            <input type="text" class="form-control editable-api-key-input" placeholder="Key name (e.g., telegram_token)" 
                   value="${escapeHtml(keyName)}" id="edit-key-name-${editableApiKeyCounter}" 
                   style="background-color: white; color: black; border: 1px solid #ccc;">
            <input type="text" class="form-control editable-api-key-input" placeholder="Key value" 
                   value="${escapeHtml(keyValue)}" id="edit-key-value-${editableApiKeyCounter}" 
                   style="background-color: white; color: black; border: 1px solid #ccc;">
            <button class="btn btn-outline-danger" type="button" onclick="removeEditableApiKeyField(${editableApiKeyCounter})">
                <i data-feather="trash-2"></i>
            </button>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', fieldHtml);
    editableApiKeyCounter++;
    feather.replace();
}

function removeEditableApiKeyField(index) {
    const field = document.getElementById(`editable-key-${index}`);
    if (field) {
        field.remove();
    }
}

function cancelApiKeysEdit() {
    // Show display, hide editor
    document.getElementById('api-keys-display').style.display = 'block';
    document.getElementById('api-keys-editor').style.display = 'none';
}

// API Keys form submission
document.addEventListener('DOMContentLoaded', function() {
    const apiKeysForm = document.getElementById('api-keys-form');
    if (apiKeysForm) {
        apiKeysForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await saveApiKeys();
        });
    }
});

async function saveApiKeys() {
    if (!currentClient) return;
    
    showLoading(true);
    try {
        // Collect API keys from form
        const apiKeys = {};
        const container = document.getElementById('editable-api-keys-container');
        const nameInputs = container.querySelectorAll('input[id^="edit-key-name-"]');
        
        nameInputs.forEach(nameInput => {
            const index = nameInput.id.split('-').pop();
            const valueInput = document.getElementById(`edit-key-value-${index}`);
            
            if (nameInput.value.trim() && valueInput.value.trim()) {
                apiKeys[nameInput.value.trim()] = valueInput.value.trim();
            }
        });
        
        const response = await fetch(`/api/clients/${currentClient.id}/api-keys`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_keys: apiKeys })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            originalApiKeys = { ...apiKeys };
            displayApiKeys(apiKeys);
            cancelApiKeysEdit();
            showNotification('API keys updated successfully!', 'success');
        } else {
            throw new Error(data.error || 'Failed to update API keys');
        }
        
    } catch (error) {
        showNotification('Error saving API keys: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function updateConversationInfo(messageCount) {
    document.getElementById('conversation-info').textContent = 
        `Session: ${currentSessionId} | Messages: ${messageCount}`;
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    feather.replace();
    fetchClients();
    loadGlobalOpenAIKey();
    
    // Deploy bot form handler
    const deployForm = document.getElementById('deploy-bot-form');
    if (deployForm) {
        deployForm.addEventListener('submit', function(e) {
            e.preventDefault();
            deployBot();
        });
    }
});

// === GLOBAL SETTINGS MANAGEMENT ===

async function loadGlobalOpenAIKey() {
    try {
        const response = await fetch('/api/settings/openai-key');
        const data = await response.json();
        
        if (response.ok) {
            const keyInput = document.getElementById('global-openai-key');
            const statusDiv = document.getElementById('key-status');
            const noBanner = document.getElementById('no-key-banner');
            
            if (keyInput && statusDiv) {
                keyInput.value = data.api_key || '';
                
                if (data.is_set) {
                    statusDiv.innerHTML = `<span class="text-success">✅ Active: ${data.masked_key}</span>`;
                    noBanner.style.display = 'none';
                } else {
                    statusDiv.innerHTML = `<span class="text-warning">⚠️ No API key configured</span>`;
                    noBanner.style.display = 'block';
                }
            }
        } else {
            console.error('Error loading OpenAI key:', data.error);
            const statusDiv = document.getElementById('key-status');
            if (statusDiv) {
                statusDiv.innerHTML = `<span class="text-danger">❌ Error loading key status</span>`;
            }
        }
    } catch (error) {
        console.error('Error loading OpenAI key:', error);
    }
}

async function saveGlobalOpenAIKey() {
    const keyInput = document.getElementById('global-openai-key');
    const apiKey = keyInput.value.trim();
    
    if (!apiKey) {
        showNotification('Please enter an API key', 'error');
        return;
    }
    
    // First attempt without confirmation to check if confirmation is required
    showLoading(true);
    try {
        let response = await fetch('/api/settings/openai-key', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey, confirmed: false })
        });
        
        let data = await response.json();
        
        if (response.ok) {
            // Success without confirmation needed
            await handleSuccessfulKeySave(data);
        } else if (data.requires_confirmation) {
            // Confirmation required - show warning and ask user
            const confirmed = confirm(
                '⚠️ WARNING: Changing the OpenAI API key will affect ALL bots across ALL clients.\n\n' +
                'If the new key is invalid, all bots will stop working until a valid key is set.\n\n' +
                'Are you sure you want to change the global OpenAI API key?'
            );
            
            if (confirmed) {
                // Send confirmed request
                response = await fetch('/api/settings/openai-key', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ api_key: apiKey, confirmed: true })
                });
                
                data = await response.json();
                
                if (response.ok) {
                    await handleSuccessfulKeySave(data);
                } else {
                    throw new Error(data.error || 'Failed to save API key');
                }
            } else {
                showNotification('API key change cancelled', 'info');
            }
        } else {
            throw new Error(data.error || 'Failed to save API key');
        }
    } catch (error) {
        showNotification('Error saving API key: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function handleSuccessfulKeySave(data) {
    showNotification(data.message || 'OpenAI API key saved and validated successfully!', 'success');
    
    // Update status display
    const statusDiv = document.getElementById('key-status');
    const noBanner = document.getElementById('no-key-banner');
    
    if (statusDiv) {
        statusDiv.innerHTML = `<span class="text-success">✅ Active: ${data.masked_key}</span>`;
    }
    
    if (noBanner) {
        noBanner.style.display = 'none';
    }
}

function toggleGlobalKeyVisibility() {
    const keyInput = document.getElementById('global-openai-key');
    const eyeIcon = document.getElementById('eye-icon');
    
    if (keyInput.type === 'password') {
        keyInput.type = 'text';
        eyeIcon.setAttribute('data-feather', 'eye-off');
    } else {
        keyInput.type = 'password';
        eyeIcon.setAttribute('data-feather', 'eye');
    }
    
    feather.replace();
}