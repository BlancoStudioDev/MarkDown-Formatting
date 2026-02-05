import requests
import json
import sys

# Impostazioni di base
BASE_URL = "http://localhost:1234"
# Il modello specificato dall'utente
TARGET_MODEL = "qwen/qwen3-vl-8b"

def check_connection(url):
    try:
        requests.get(f"{url}/api/v1/models", timeout=2)
        return True
    except:
        return False

def get_base_url():
    """Determina l'URL corretto (localhost o 127.0.0.1)."""
    if check_connection("http://localhost:1234"):
        return "http://localhost:1234"
    if check_connection("http://127.0.0.1:1234"):
        return "http://127.0.0.1:1234"
    return None

def get_models():
    """Recupera la lista dei modelli disponibili."""
    base_url = get_base_url()
    if not base_url:
        print("Could not connect to LM Studio on port 1234 (tried localhost and 127.0.0.1).")
        print("Please ensure:")
        print("1. LM Studio is open.")
        print("2. The 'Local Server' feature is started (green banner).")
        print("3. Port is set to 1234.")
        return None

    global BASE_URL
    BASE_URL = base_url
    
    # Try the OpenAI compatible endpoint first
    try:
        response = requests.get(f"{BASE_URL}/v1/models")
        if response.status_code == 200:
            print(f"Successfully connected to {BASE_URL}")
            return response.json()
    except Exception:
        pass

    # Fallback to the one user listed
    try:
        response = requests.get(f"{BASE_URL}/api/v1/models")
        if response.status_code == 200:
            print(f"Successfully connected to {BASE_URL}")
            return response.json()
        else:
            print(f"Error retrieving models: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Connection error: {e}")
        return None

def chat_with_model(model_id, prompt):
    """Invia un messaggio al modello e stampa la risposta."""
    # Use standard OpenAI chat completion endpoint
    url = f"{BASE_URL}/v1/chat/completions"
    
    # Payload standard per chat
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": -1,
        "stream": False
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    print(f"Sending request to {url} with model {model_id}...")
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            result = response.json()
            try:
                content = result['choices'][0]['message']['content']
                print("\n--- AI Response ---")
                print(content)
                print("-------------------\n")
                return content
            except KeyError:
                print("Response format might be different than expected:")
                print(json.dumps(result, indent=2))
                return result
        else:
            print(f"Error in chat request: {response.status_code}")
            print(response.text)
            # Fallback for error debugging
            return None
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None

def main():
    print("--- LM Studio Client ---")
    
    # 1. List Models
    models_data = get_models()
    if not models_data:
        return

    # Debug: print available models format
    # print(json.dumps(models_data, indent=2))
    
    # Check if our target model is available
    # LM Studio API structure for models usually contains a 'data' list
    available_models = []
    if 'data' in models_data:
        available_models = [m['id'] for m in models_data['data']]
    
    print(f"Available models: {available_models}")
    
    # Use target model or pick the first one
    model_to_use = TARGET_MODEL
    
    # NOTE: Sometimes the ID in the list might be slightly different (e.g. full path), 
    # but let's try to use the one requested or fall back to the first available if not found exactly.
    if model_to_use not in available_models and available_models:
        print(f"Warning: {model_to_use} not explicitly found in list. Using {available_models[0]} instead.")
        model_to_use = available_models[0]
    elif not available_models:
        print("No models found via API. Trying detailed name anyway.")
    
    print(f"Using model: {model_to_use}")

    # 2. Chat Loop
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        
        chat_with_model(model_id=model_to_use, prompt=user_input)

if __name__ == "__main__":
    main()
