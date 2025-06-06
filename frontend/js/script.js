// Global variables and functions
let userId = null;
let currentState = 'start';
let isRegistered = false;
let recognition = null;
let selectedFile = null;

function fetchChatResponse(state, input) {
    console.log('Fetching chat response for state:', state, 'with input:', input); // Debug log
    fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state, input, user_id: userId })
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        console.log('Server response:', data); // Debug log
        addMessage(data.response, 'bot');
        currentState = data.next_state;

        if (data.options && data.options.length > 0) {
            displayOptions(data.options, data.next_state);
        } else if (data.next_state === 'question') {
            addMessage('Type your question below:', 'bot');
        } else if (data.options.length === 0 && data.next_state !== state) {
            fetchChatResponse(data.next_state, '');
        }

        scrollToBottom();
    })
    .catch(error => {
        console.error('Chat error:', error);
        addMessage('Sorry, something went wrong. Let’s get back on track.', 'bot');
        currentState = 'category_selected';
        fetchChatResponse('category_selected', '');
        scrollToBottom();
    });
}

function addMessage(text, sender) {
    if (!text && sender === 'bot') return;
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);
    messageDiv.textContent = text;
    document.getElementById('messagesContainer').appendChild(messageDiv);
    scrollToBottom();
}

function scrollToBottom() {
    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Single DOMContentLoaded listener
document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const chatbotBtn = document.getElementById('chatbotBtn');
    const chatbotLabel = document.getElementById('chatbotLabel');
    const chatbotPopup = document.getElementById('chatbotPopup');
    const closeChat = document.getElementById('closeChat');
    const sendBtn = document.getElementById('sendBtn');
    const userInput = document.getElementById('userInput');
    const registrationForm = document.getElementById('registrationForm');
    const chatbotBody = document.getElementById('chatbotBody');
    const messagesContainer = document.getElementById('messagesContainer');
    const startChatBtn = document.getElementById('startChatBtn');
    const userName = document.getElementById('userName');
    const userMobile = document.getElementById('userMobile');
    const voiceBtn = document.getElementById('voiceBtn');
    const attachBtn = document.getElementById('attachBtn');
    const fileInput = document.getElementById('fileInput');
    const refreshButton = document.getElementById('refreshChat');

    // Check if critical elements exist
    if (!refreshButton) console.error('Refresh button not found in DOM');
    if (!messagesContainer) console.error('Messages container not found in DOM');

    function initVoiceRecognition() {
        try {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SpeechRecognition) {
                recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                
                recognition.onresult = event => {
                    userInput.value = event.results[0][0].transcript;
                    voiceBtn.classList.remove('listening');
                };
                
                recognition.onerror = event => {
                    console.error('Speech recognition error', event.error);
                    voiceBtn.classList.remove('listening');
                };
                
                recognition.onend = () => voiceBtn.classList.remove('listening');
                
                voiceBtn.style.display = 'flex';
                return true;
            }
        } catch (e) {
            console.error("Speech recognition init error:", e);
        }
        voiceBtn.style.display = 'none';
        return false;
    }

    const voiceSupported = initVoiceRecognition();

    // Refresh button handler
    refreshButton.addEventListener('click', function() {
        console.log('Refresh button clicked'); // Debug log
        messagesContainer.innerHTML = '';
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) welcomeMessage.classList.remove('d-none');
        this.classList.add('refreshing');
        setTimeout(() => this.classList.remove('refreshing'), 500);
        currentState = 'start';
        addMessage("Chat refreshed. Let's start over.", 'bot');
        fetchChatResponse('start', '');
    });

    chatbotBtn.addEventListener('click', function() {
        chatbotPopup.classList.toggle('active');
        chatbotLabel.style.opacity = '0';
        chatbotLabel.style.visibility = 'hidden';
        this.classList.add('animate-bounce');
        setTimeout(() => this.classList.remove('animate-bounce'), 300);
    });

    closeChat.addEventListener('click', function() {
        chatbotPopup.classList.remove('active');
        setTimeout(() => {
            chatbotLabel.style.opacity = '1';
            chatbotLabel.style.visibility = 'visible';
        }, 300);
        if (recognition && voiceBtn.classList.contains('listening')) recognition.stop();
    });

    startChatBtn.addEventListener('click', function() {
        const name = userName.value.trim();
        const mobile = userMobile.value.trim();
        if (name && mobile && mobile.length === 10 && /^\d+$/.test(mobile)) {
            fetch('http://localhost:5000/register', {
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
                    alert(data.message + ' (OTP: ' + data.otp + ')');
                    const otpDiv = document.createElement('div');
                    otpDiv.innerHTML = `
                        <input type="text" id="otpInput" class="form-control" placeholder="Enter OTP">
                        <button id="verifyOtpBtn" class="btn btn-primary mt-2">Verify OTP</button>
                    `;
                    registrationForm.appendChild(otpDiv);
                    document.getElementById('verifyOtpBtn').addEventListener('click', () => verifyOtp(userId));
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Registration fetch error:', error);
                alert('Registration failed. Please try again.');
            });
        } else {
            alert('Please enter a valid name and 10-digit mobile number.');
        }
    });

    function verifyOtp(userId) {
        const otp = document.getElementById('otpInput').value.trim();
        if (otp) {
            fetch('http://localhost:5000/verify_otp', {
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
                    registrationForm.classList.add('d-none');
                    chatbotBody.classList.remove('d-none');
                    startChatbot();
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('OTP verification fetch error:', error);
                alert('OTP verification failed. Please try again.');
            });
        } else {
            alert('Please enter the OTP.');
        }
    }

    function startChatbot() {
        addMessage("Hello! I'm your T.I.M.E. assistant. Let's get started.", 'bot');
        fetchChatResponse('start', '');
    }

    function displayOptions(options, nextState) {
        const optionsDiv = document.createElement('div');
        optionsDiv.classList.add('prompts-inline');
        options.forEach(option => {
            const button = document.createElement('button');
            button.textContent = option;
            button.classList.add('option-btn');
            button.addEventListener('click', () => {
                addMessage(option, 'user');
                fetchChatResponse(nextState, option);
                optionsDiv.remove();
            });
            optionsDiv.appendChild(button);
        });
        messagesContainer.appendChild(optionsDiv);
        scrollToBottom();
    }

    function sendMessage() {
        if (!isRegistered) return;
        const message = userInput.value.trim();
        if (message || selectedFile) {
            if (message) {
                addMessage(message, 'user');
                if (currentState === 'question') {
                    fetchChatResponse(currentState, message);
                } else {
                    addMessage("Please select an option or wait for the next prompt.", 'bot');
                }
            }
            if (selectedFile) addFilePreview(selectedFile);
            userInput.value = '';
            selectedFile = null;
            fileInput.value = '';
            scrollToBottom();
        }
    }

    function addFilePreview(file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const filePreview = document.createElement('div');
            filePreview.classList.add('message', 'user-message');
            if (file.type.startsWith('image/')) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.classList.add('attachment-preview');
                filePreview.appendChild(img);
            } else {
                const fileInfo = document.createElement('div');
                fileInfo.textContent = `Attachment: ${file.name}`;
                filePreview.appendChild(fileInfo);
            }
            messagesContainer.appendChild(filePreview);
            scrollToBottom();
        };
        reader.readAsDataURL(file);
    }

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', e => e.key === 'Enter' && sendMessage());

    voiceBtn.addEventListener('click', function() {
        if (!isRegistered) return alert('Please register first');
        if (recognition) {
            if (voiceBtn.classList.contains('listening')) {
                recognition.stop();
            } else {
                try {
                    recognition.start();
                    voiceBtn.classList.add('listening');
                    userInput.placeholder = "Listening...";
                    setTimeout(() => userInput.placeholder = "Type your question...", 3000);
                } catch (e) {
                    console.error('Voice recognition error:', e);
                    voiceBtn.classList.remove('listening');
                }
            }
        } else {
            alert("Voice search is not supported in your browser");
        }
    });

    attachBtn.addEventListener('click', function() {
        if (!isRegistered) return alert('Please register first');
        fileInput.click();
    });

    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                selectedFile = this.files[0];
                userInput.placeholder = `File attached: ${selectedFile.name}`;
                setTimeout(() => userInput.placeholder = "Type your question...", 3000);
            }
        });
    } else {
        console.error('Element with ID "fileInput" not found in the DOM.');
    }

    // Wave animation for chatbot button
    let animationCount = 0;
    const maxAnimations = 3;
    function triggerWaveAnimation() {
        if (animationCount >= maxAnimations) return;
        chatbotBtn.classList.add('wave-effect');
        animationCount++;
        setTimeout(() => {
            chatbotBtn.classList.remove('wave-effect');
            setTimeout(triggerWaveAnimation, 300);
        }, 1500);
    }
    triggerWaveAnimation();

    setTimeout(() => {
        chatbotBtn.classList.add('animate-bounce');
        setTimeout(() => chatbotBtn.classList.remove('animate-bounce'), 1000);
    }, 1500);

    console.log('Voice recognition supported:', voiceSupported);
});