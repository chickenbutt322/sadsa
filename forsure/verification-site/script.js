
document.addEventListener('DOMContentLoaded', function() {
    const resultDiv = document.getElementById('result');
    const manualSection = document.getElementById('manualVerification');
    const messageText = document.getElementById('messageText');
    const headerText = document.getElementById('headerText');

    // Extract token from URL
    const urlParams = new URLSearchParams(window.location.search);
    const urlToken = urlParams.get('token');

    function showResult(message, type) {
        resultDiv.innerHTML = message;
        resultDiv.className = `result ${type}`;
        resultDiv.style.display = 'block';
        messageText.textContent = '';
    }

    function showLoading() {
        showResult('<span class="loading"></span>Verifying your email...', 'info');
    }

    async function verifyToken(token) {
        if (!token || token.trim() === '') {
            showResult('❌ Please enter a valid verification token.', 'error');
            return;
        }

        showLoading();

        try {
            // Get the current hostname and construct the Flask app URL
            const hostname = window.location.hostname;
            let flaskUrl;
            
            // Handle different deployment scenarios
            if (hostname.includes('netlify.app') || hostname.includes('vercel.app')) {
                // For Netlify/Vercel deployments, try to guess the Flask app URL
                // You might need to update this with your actual Flask app URL
                flaskUrl = 'https://your-flask-app-url.replit.dev';
            } else if (hostname.includes('replit.dev') || hostname.includes('replit.co')) {
                // For Replit preview URLs
                const parts = hostname.split('-');
                if (parts.length > 1) {
                    flaskUrl = `https://3000-${parts.slice(1).join('-')}`;
                } else {
                    flaskUrl = `https://3000-${hostname}`;
                }
            } else {
                // Fallback for local development
                flaskUrl = 'http://localhost:3000';
            }

            console.log('Attempting to verify with URL:', `${flaskUrl}/verify-email/${token}`);

            // Try to verify the token
            const response = await fetch(`${flaskUrl}/verify-email/${token}`, {
                method: 'GET',
                headers: {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Content-Type': 'application/json'
                },
                mode: 'cors'
            });

            if (response.ok) {
                const responseText = await response.text();
                
                if (responseText.includes('Email verified successfully') || 
                    responseText.includes('verified') || 
                    response.status === 200) {
                    
                    showResult('✅ Email verified successfully! You can now log in to your account.', 'success');
                    
                    // Redirect to login page after a delay
                    setTimeout(() => {
                        window.location.href = `${flaskUrl}/login`;
                    }, 3000);
                } else {
                    showResult('❌ Invalid or expired verification token. Please check your email and try again.', 'error');
                }
            } else {
                if (response.status === 404) {
                    showResult('❌ Invalid verification token. Please check your email and try again.', 'error');
                } else if (response.status === 400) {
                    showResult('❌ This verification link has expired. Please request a new verification email.', 'error');
                } else {
                    showResult('❌ Unable to verify email at this time. Please try again later.', 'error');
                }
            }
        } catch (error) {
            console.error('Verification error:', error);
            
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                showResult('❌ Unable to connect to the verification server. Please check your internet connection and try again.', 'error');
            } else {
                showResult('❌ An unexpected error occurred. Please try again later or contact support.', 'error');
            }
        }
    }

    // Function to handle manual token verification
    window.verifyToken = function() {
        const token = document.getElementById('tokenInput').value.trim();
        verifyToken(token);
    };

    // Handle Enter key press in token input
    document.getElementById('tokenInput')?.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            window.verifyToken();
        }
    });

    // Initialize the page based on whether token is in URL
    if (urlToken && urlToken.trim() !== '') {
        // Auto-verify if token is in URL
        headerText.textContent = 'Verifying Email Address';
        messageText.textContent = 'Please wait while we verify your email...';
        manualSection.style.display = 'none';
        
        // Add a small delay to show the loading state
        setTimeout(() => {
            verifyToken(urlToken);
        }, 1000);
    } else {
        // Show manual verification form
        headerText.textContent = 'Email Verification';
        messageText.textContent = 'Enter your verification token below to verify your email address.';
        manualSection.style.display = 'block';
    }
});
