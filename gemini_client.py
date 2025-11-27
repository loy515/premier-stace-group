import google.generativeai as genai
import google.auth

# --- CONFIGURATION ---
SERVICE_ACCOUNT_FILE = 'service-account-key.json'

# --- AUTHENTICATION ---
try:
    credentials, _ = google.auth.load_credentials_from_file(SERVICE_ACCOUNT_FILE)
    genai.configure(transport="rest", credentials=credentials)
    model = genai.GenerativeModel('gemini-2.5-pro') # Use the correct, available model
    print("✅ Gemini AI Client Initialized Successfully.")
except Exception as e:
    print(f"❌ Gemini AI Client Failed to Initialize: {e}")
    model = None

# --- FUNCTIONS ---
def verify_address_with_ai(unverified_address: str) -> str:
    if model is None: return "AI Model is not available. Check server logs."
    if not unverified_address: return "No address provided."

    prompt = f"""
    You are an expert logistics address verification system.
    Analyze the following user-provided shipping address and return ONLY a corrected, standardized, and properly formatted version suitable for a shipping label.
    - Correct spelling mistakes. Add missing components like country (default to USA).
    - Format it as a standard multi-line address.
    - If the address is invalid, return a single line explaining why.

    User Address: "{unverified_address}"
    Corrected Address:
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"AI VERIFICATION ERROR: {e}")
        return "Error during AI verification. See server logs."
