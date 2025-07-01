// Global variables
let userId = null;
let currentState = 'start';
let isRegistered = false;
let allOptions = []; // Store all options for filtering
let optionsDiv = null; // Reference to the options container
let cityOptions = []; // Store city options for filtering
let chatMode = 'flow'; // 'flow' or 'rag' - default to flow-based chat

// Function to add messages to the chat
function addMessage(text, sender) {
    if (!text && sender === 'bot') return;
    const messagesContainer = document.getElementById('messagesContainer');
    if (!messagesContainer) {
        console.error('Messages container not found');
        return;
    }
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);
    messageDiv.innerHTML = text; // Use innerHTML to render HTML
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Function to display options
function displayOptions(options, nextState, backOptions = []) {
    const messagesContainer = document.getElementById('messagesContainer');
    const userInput = document.getElementById('userInput');
    if (!messagesContainer || !userInput) {
        console.error('Messages container or user input not found');
        return;
    }
    // Ensure options and backOptions are arrays
    const safeOptions = Array.isArray(options) ? options : [];
    const safeBackOptions = Array.isArray(backOptions) ? backOptions : [];
    allOptions = safeOptions.concat(safeBackOptions); // Combine regular and back options
    if (!allOptions.length) {
        // No options to display; clear any existing optionsDiv
        if (optionsDiv) {
            optionsDiv.remove();
            optionsDiv = null;
        }
        return;
    }
    if (optionsDiv) {
        optionsDiv.remove(); // Remove previous optionsDiv if exists
        optionsDiv = null;
    }
    optionsDiv = document.createElement('div');
    optionsDiv.classList.add('prompts-inline');
    renderOptions(safeOptions, safeBackOptions, nextState);
    messagesContainer.appendChild(optionsDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    userInput.value = ''; // Clear input on new options
}

// Function to render filtered options
function renderOptions(options, backOptions, nextState) {
    if (!optionsDiv) return;
    optionsDiv.innerHTML = '';
    // Render regular options first
    options.forEach(option => {
        const button = document.createElement('button');
        button.textContent = option;
        button.classList.add('option-btn');
        button.addEventListener('click', () => {
            addMessage(option, 'user');
            fetchChatResponse(nextState, option);
            if (optionsDiv) {
                optionsDiv.remove();
                optionsDiv = null;
            }
            allOptions = [];
            document.getElementById('userInput').value = '';
        });
        optionsDiv.appendChild(button);
    });
    // Render back options last (e.g., "Back", "Main page")
    backOptions.forEach(option => {
        const button = document.createElement('button');
        // Display "Back" for any "Back to ..." option, keep "Main page" as-is
        button.textContent = option.startsWith('Back to') ? 'Back' : option;
        button.classList.add('back-btn'); // Only add back-btn class
        button.addEventListener('click', () => {
            addMessage(option, 'user');
            fetchChatResponse(nextState, option);
            // Conversation Tree (removable): update tree after user selection
            if (window.TreeModule) {
                console.log('[Chatbot] Attempting to call TreeModule.addNode with:', option, nextState);
                window.TreeModule.addNode({
                    label: option,
                    previousState: nextState,
                    nextState: nextState,
                    options: [],
                    previousLabel: '',
                    path: data.path // Use the path returned from backend
                });
            }
            if (optionsDiv) {
                optionsDiv.remove();
                optionsDiv = null;
            }
            allOptions = [];
            document.getElementById('userInput').value = '';
        });
        optionsDiv.appendChild(button);
    });
}

// Function to filter options based on input
function filterOptions(input) {
    if (currentState === 'city_selected') {
        if (!cityOptions || cityOptions.length === 0) return;
        const filteredCities = input ? cityOptions.filter(city => 
            city.toLowerCase().includes(input.toLowerCase())
        ) : [];
        displayCityOptions(filteredCities);
    } else {
        if (!allOptions.length || !optionsDiv) return;
        const filteredOptions = allOptions.filter(option => 
            option.toLowerCase().includes(input.toLowerCase())
        );
        const regularOptions = filteredOptions.filter(opt => !opt.startsWith('Back to') && opt !== 'Main page');
        const backOptions = filteredOptions.filter(opt => opt.startsWith('Back to') || opt === 'Main page');
        renderOptions(regularOptions, backOptions, currentState);
    }
}

// Function to display city options as prompts
function displayCityOptions(cities) {
    const messagesContainer = document.getElementById('messagesContainer');
    if (!messagesContainer) return;
    if (optionsDiv) {
        optionsDiv.remove();
        optionsDiv = null;
    }
    if (cities.length === 0) return;
    optionsDiv = document.createElement('div');
    optionsDiv.classList.add('prompts-inline');
    cities.forEach(city => {
        const button = document.createElement('button');
        button.textContent = city;
        button.classList.add('option-btn');
        button.addEventListener('click', () => {
            addMessage(city, 'user');
            fetchChatResponse(currentState, city);
            if (optionsDiv) {
                optionsDiv.remove();
                optionsDiv = null;
            }
            document.getElementById('userInput').value = '';
        });
        optionsDiv.appendChild(button);
    });
    messagesContainer.appendChild(optionsDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Function to fetch chat responses from the server
function fetchChatResponse(state, input) {
    const payload = {
        state,
        input: input || '',
        user_id: userId
    };
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Network response was not ok: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (!data || typeof data.response === 'undefined') {
            throw new Error('Invalid backend response');
        }
        addMessage(data.response, 'bot');
        currentState = data.next_state;
        // Conversation Tree (removable): update tree after response from server
        if (window.TreeModule && input) { // only run if there was user input
            window.TreeModule.addNode({
                label: input,
                previousState: state,
                nextState: data.next_state,
                options: data.options || [],
                path: data.path // Use the path returned from backend
            });
        }
        // Fetch cities when entering city_selected state
        if (currentState === 'city_selected') {
            fetch('/api/all_cities')
                .then(response => response.json())
                .then(cityData => {
                    if (cityData.success) {
                        cityOptions = cityData.data;
                    } else {
                        console.error('Failed to fetch cities:', cityData.error);
                    }
                })
                .catch(error => console.error('Error fetching cities:', error));
        }
        displayOptions(data.options || [], data.next_state, data.back_options || []);
    })
    .catch(error => {
        console.error('Fetch error details:', error);
        addMessage('Oops, something went wrong. Restarting...', 'bot');
        currentState = 'start';
        fetchChatResponse('start', '');
    });
}

// Function to handle registration
function handleRegistration() {
    const nameInput = document.getElementById('userName');
    const mobileInput = document.getElementById('userMobile');
    
    if (!nameInput || !mobileInput) {
        console.error('Registration inputs not found');
        return;
    }

    const name = nameInput.value.trim();
    const mobile = mobileInput.value.trim();

    if (!name || !mobile || mobile.length !== 10 || !/^\d+$/.test(mobile)) {
        alert('Please enter a valid name and 10-digit mobile number');
        return;
    }

    fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, mobile })
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (data.success) {
            userId = data.user_id;
            window.userId = userId; // Set globally for tree
            alert(`Registration successful! OTP: ${data.otp}`);
            const registrationForm = document.getElementById('registrationForm');
            if (registrationForm) {
                registrationForm.innerHTML = `
                    <div class="welcome-message">Enter OTP sent to your mobile</div>
                    <div class="mb-3">
                        <input type="text" class="form-control" id="otpInput" placeholder="Enter OTP">
                    </div>
                    <button class="btn btn-primary" id="verifyOtpBtn">Verify OTP</button>
                `;
                document.getElementById('verifyOtpBtn').onclick = verifyOTP;
            }
        } else {
            alert(data.message || 'Registration failed. Please try again.');
        }
    })
    .catch(error => {
        console.error('Registration error:', error);
        alert('Registration failed. Please try again.');
    });
}

// Function to verify OTP
function verifyOTP() {
    const otpInput = document.getElementById('otpInput');
    if (!otpInput) {
        console.error('OTP input not found');
        return;
    }

    const otp = otpInput.value.trim();
    if (!otp) {
        alert('Please enter the OTP');
        return;
    }

    fetch('/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, otp })
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (data.success) {
            isRegistered = true;
            window.userId = userId; // Ensure it's still set globally
            const registrationForm = document.getElementById('registrationForm');
            const chatbotBody = document.getElementById('chatbotBody');
            if (registrationForm && chatbotBody) {
                registrationForm.classList.add('d-none');
                chatbotBody.classList.remove('d-none');
            }
            document.getElementById('chatInputContainer').classList.remove('d-none');
            addMessage("Hello! I'm your T.I.M.E. assistant. Let's get started.", 'bot');
            fetchChatResponse('start', '');
        } else {
            alert(data.message || 'Invalid OTP. Please try again.');
        }
    })
    .catch(error => {
        console.error('OTP verification error:', error);
        alert('OTP verification failed. Please try again.');
    });
}

// Function to reset and refresh the chat
function refreshChat() {
    const messagesContainer = document.getElementById('messagesContainer');
    const userInput = document.getElementById('userInput');
    if (messagesContainer) {
        messagesContainer.innerHTML = '';
    } else {
        console.error('Messages container not found during refresh');
    }
    if (userInput) {
        userInput.value = ''; // Clear input
    }
    if (optionsDiv) {
        optionsDiv.remove();
        optionsDiv = null;
        allOptions = [];
    }
    currentState = 'start';
    fetchChatResponse('start', '');
}

// Function to toggle chat popup
function toggleChat() {
    const popup = document.getElementById('chatbotPopup');
    const btnContainer = document.getElementById('chatbotBtnContainer');
    if (popup && btnContainer) {
        popup.classList.toggle('active');
        btnContainer.classList.toggle('active');
    }
}

// Function to send user input to the backend
function sendMessage() {
    const userInput = document.getElementById('userInput');
    if (!userInput) {
        console.error('User input not found');
        return;
    }
    const input = userInput.value.trim();
    if (input) {
        addMessage(input, 'user');
        
        if (chatMode === 'rag') {
            // Use RAG-based chat
            fetchRAGResponse(input);
        } else {
            // Use flow-based chat
            fetchChatResponse(currentState, input);
        }
        
        userInput.value = '';
    }
}

// Function to fetch RAG responses from the server
function fetchRAGResponse(message) {
    const payload = {
        message: message,
        user_id: userId
    };
    
    fetch('/rag-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Network response was not ok: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        addMessage(data.response, 'bot');
    })
    .catch(error => {
        console.error('RAG fetch error:', error);
        addMessage('Oops, something went wrong with the AI response. Please try again.', 'bot');
    });
}

// Function to toggle between flow-based and RAG-based chat
function toggleChatMode() {
    console.log('Toggle chat mode clicked. Current mode:', chatMode);
    
    chatMode = chatMode === 'flow' ? 'rag' : 'flow';
    console.log('Switched to mode:', chatMode);
    
    // Update UI to show current mode
    const modeIndicator = document.getElementById('chatModeIndicator');
    if (modeIndicator) {
        modeIndicator.textContent = chatMode === 'rag' ? 'AI Chat' : 'Flow Chat';
        modeIndicator.className = chatMode === 'rag' ? 'mode-indicator rag-mode' : 'mode-indicator flow-mode';
        console.log('Updated mode indicator:', modeIndicator.textContent);
    } else {
        console.error('Mode indicator not found');
    }
    
    // Clear current conversation when switching modes
    const messagesContainer = document.getElementById('messagesContainer');
    if (messagesContainer) {
        messagesContainer.innerHTML = '';
        console.log('Cleared messages container');
    } else {
        console.error('Messages container not found');
    }
    
    if (optionsDiv) {
        optionsDiv.remove();
        optionsDiv = null;
        allOptions = [];
        console.log('Cleared options');
    }
    
    // Reset state for flow mode
    if (chatMode === 'flow') {
        currentState = 'start';
        console.log('Switched to flow mode, starting flow chat');
        fetchChatResponse('start', '');
    } else {
        // Welcome message for RAG mode
        console.log('Switched to RAG mode, showing welcome message');
        addMessage("Hello! I'm TINA, your AI assistant. I can help you with questions about T.I.M.E. courses, exams, admissions, and more. Feel free to ask me anything!", 'bot');
    }
}

// Initialize the chat when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded'); // Debug log
    const sendButtonCheck = document.getElementById('sendButton');
    console.log('Send button element:', sendButtonCheck); // Debug log

    const chatbotBtn = document.getElementById('chatbotBtn');
    if (chatbotBtn) {
        chatbotBtn.onclick = toggleChat;
    } else {
        console.error('Chatbot button not found in DOM');
    }

    const closeBtn = document.getElementById('closeChat');
    if (closeBtn) {
        closeBtn.onclick = toggleChat;
    } else {
        console.error('Close button not found in DOM');
    }

    const refreshButton = document.getElementById('refreshChat');
    if (refreshButton) {
        refreshButton.onclick = refreshChat;
    } else {
        console.error('Refresh button not found in DOM');
    }

    const startChatBtn = document.getElementById('startChatBtn');
    if (startChatBtn) {
        startChatBtn.onclick = handleRegistration;
    } else {
        console.error('Start chat button not found in DOM');
    }

    const userInput = document.getElementById('userInput');
    if (userInput) {
        userInput.addEventListener('input', () => {
            filterOptions(userInput.value);
        });
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    } else {
        console.error('User input not found in DOM');
    }

    const sendButton = document.getElementById('sendButton');
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    } else {
        console.error('Send button not found in DOM');
    }

    // --- Conversation Tree Event Listeners (removable) ---

    // Listen for the tree telling the chatbot to rewind to a previous state
    window.addEventListener('tree:rewind', (e) => {
        console.log('[Chatbot] Received tree:rewind event. Details:', e.detail);
        const { label, state, context } = e.detail;

        // Clear existing messages and options
        const messagesContainer = document.getElementById('messagesContainer');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
        if (optionsDiv) {
            optionsDiv.remove();
            optionsDiv = null;
        }

        // Add a message indicating the rewind
        addMessage(`Rewinding to "${label}"...`, 'bot');

        // Call the backend with the old state to get the options for that point in the conversation
        // Note: We pass an empty string for the 'input' because we are not selecting a new option,
        // but rather re-fetching the state *after* the 'label' was originally selected.
        fetchChatResponse(state, '');
    });

    // Listen for the tree telling the chatbot to jump to a new branch
    window.addEventListener('tree:branch-jump', function(e) {
        const detail = e.detail;
        // Only call fetchChatResponse if state is valid and non-empty
        if (detail && detail.state && detail.state !== '') {
            fetchChatResponse(detail.state, detail.label);
        } else {
            console.warn('[Chatbot] Ignoring branch jump with invalid or empty state:', detail);
        }
    });
    const chatModeToggle = document.getElementById('chatModeToggle');
    if (chatModeToggle) {
        console.log('Found chat mode toggle button, adding event listener');
        chatModeToggle.addEventListener('click', toggleChatMode);
        console.log('Event listener added to chat mode toggle');
    } else {
        console.error('Chat mode toggle button not found in DOM');
        // Try to find it by different selectors
        const alternativeToggle = document.querySelector('.btn-mode-toggle');
        if (alternativeToggle) {
            console.log('Found alternative toggle button, adding event listener');
            alternativeToggle.addEventListener('click', toggleChatMode);
        } else {
            console.error('No toggle button found with any selector');
        }
    }
});