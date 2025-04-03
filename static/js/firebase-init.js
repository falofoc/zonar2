// static/js/firebase-init.js

import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-auth.js";

// TODO: Replace with your actual Firebase config, ideally loaded from environment variables
// Never commit API keys directly to your repository
const firebaseConfig = {
  apiKey: "AIzaSyCqw800Fjd4QCmbPABC11vYiquI64tNtrs", // Replace with your API Key
  authDomain: "zonar-1ceee.firebaseapp.com",
  projectId: "zonar-1ceee",
  storageBucket: "zonar-1ceee.firebasestorage.app",
  messagingSenderId: "222035611921",
  appId: "1:222035611921:web:623b478663058fc8eebcb0",
  measurementId: "G-FXVQJPW9XR"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Export auth instance to be used by other modules
export { auth }; 