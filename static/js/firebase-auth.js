// static/js/firebase-auth.js

import { auth } from './firebase-init.js';
import { 
    GoogleAuthProvider, 
    signInWithPopup, 
    signOut 
} from "https://www.gstatic.com/firebasejs/11.6.0/firebase-auth.js";

const googleSignInBtn = document.getElementById('google-signin-btn');

// Function to handle server-side authentication with ID token
async function authenticateWithServer(idToken) {
    try {
        console.log("Sending ID token to server...");
        const response = await fetch('/firebase_auth', { // New endpoint for Firebase auth
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Include CSRF token if your app uses it
                // 'X-CSRFToken': getCsrfToken() 
            },
            body: JSON.stringify({ id_token: idToken })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            console.log("Server authentication successful, redirecting...");
            // Redirect to home page or dashboard on successful login
            window.location.href = data.redirect_url || '/'; 
        } else {
            console.error("Server authentication failed:", data.error);
            // Show error message to the user (you might need a dedicated UI element for this)
            alert("Authentication failed: " + (data.error || "Unknown error"));
        }
    } catch (error) {
        console.error("Error during server authentication:", error);
        alert("An error occurred during authentication. Please try again.");
    }
}

// Google Sign-In Logic
if (googleSignInBtn) {
    googleSignInBtn.addEventListener('click', async () => {
        const provider = new GoogleAuthProvider();
        
        // Optional: Add custom parameters or scopes
        // provider.addScope('profile');
        // provider.addScope('email');

        try {
            console.log("Attempting Google Sign-In popup...");
            const result = await signInWithPopup(auth, provider);
            
            // This gives you a Google Access Token. You can use it to access the Google API.
            // const credential = GoogleAuthProvider.credentialFromResult(result);
            // const token = credential.accessToken;
            
            // The signed-in user info.
            const user = result.user;
            console.log("Firebase Google Sign-In successful for:", user.displayName || user.email);
            
            // Get the Firebase ID token
            const idToken = await user.getIdToken();
            
            // Send the ID token to your backend for verification and session creation
            await authenticateWithServer(idToken);
            
        } catch (error) {
            // Handle Errors here.
            const errorCode = error.code;
            const errorMessage = error.message;
            // The email of the user's account used.
            const email = error.customData?.email;
            // The AuthCredential type that was used.
            const credential = GoogleAuthProvider.credentialFromError(error);

            console.error("Firebase Google Sign-In Error:");
            console.error("Code:", errorCode);
            console.error("Message:", errorMessage);
            console.error("Email:", email);
            
            // Provide user feedback
            if (errorCode === 'auth/popup-closed-by-user') {
                alert('Sign-in popup closed before completion.');
            } else if (errorCode === 'auth/account-exists-with-different-credential') {
                 alert('An account already exists with the same email address but different sign-in credentials. Sign in using a provider associated with this email address.');
            } else {
                alert('Google Sign-In failed. Please try again. Error: ' + errorMessage);
            }
        }
    });
}

// Optional: Add sign-out logic if needed elsewhere
// async function signOutUser() {
//     try {
//         await signOut(auth);
//         console.log('User signed out from Firebase');
//         // Redirect or update UI after sign out
//         window.location.href = '/logout'; // Example: Call your backend logout
//     } catch (error) {
//         console.error('Firebase Sign Out Error', error);
//     }
// }

// Example of getting CSRF token if needed (adjust based on your framework)
// function getCsrfToken() {
//     const csrfInput = document.querySelector('input[name="csrf_token"]');
//     return csrfInput ? csrfInput.value : null;
// } 