// Global variables
let userId = null;
let currentState = 'start';
let isRegistered = false;
let allOptions = []; // Store all options for filtering
let optionsDiv = null; // Reference to the options container

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
            addMessage(option, 'user'); // Send original option (e.g., "Back to courses") to backend
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
}

// Function to filter options based on input
function filterOptions(input) {
    if (!allOptions.length || !optionsDiv) return;
    const filteredOptions = allOptions.filter(option => 
        option.toLowerCase().includes(input.toLowerCase())
    );
    const regularOptions = filteredOptions.filter(opt => !opt.startsWith('Back to') && opt !== 'Main page');
    const backOptions = filteredOptions.filter(opt => opt.startsWith('Back to') || opt === 'Main page');
    renderOptions(regularOptions, backOptions, currentState);
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
        addMessage(data.response, 'bot');
        currentState = data.next_state;
        // Ensure options and back_options are arrays
        displayOptions(data.options || [], data.next_state, data.back_options || []);
    })
    .catch(error => {
        console.error('Fetch error:', error);
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
        fetchChatResponse(currentState, input);
        userInput.value = '';
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
});