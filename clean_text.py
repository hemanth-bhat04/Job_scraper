import requests
import json
import os

# ====== CONFIG ======
TRANSCRIPT_PATH = "video_segments/design_of_mux.txt"
API_KEY = "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"
MODEL = "meta-llama/llama-3.1-8b-instruct:free"

# ====== LOAD RAW TRANSCRIPT ======
with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
    raw_text = f.read().strip()

# ====== STRONG PROMPT INSTRUCTIONS ======
system_message = (
    "You are a strict grammar correction engine. "
    "Fix only grammar, punctuation, and sentence structure. "
    "Do not change acronyms, technical terms, or numbers. "
    "Very stricty-Return ONLY the corrected transcript — no explanations, no headings, no notes."
)

user_prompt = (
    "Correct the following transcript text. "
    "Fix only grammar, punctuation, and sentence flow. "
    "Do not touch acronyms, numbers, or domain-specific words." 
    "Return only the corrected version. Do not say 'Here is the corrected text' or anything else.\n\n"
    + raw_text
)

# ====== HEADERS & PAYLOAD ======
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt}
    ]
}

# ====== API REQUEST & SAFE RESPONSE HANDLING ======
try:
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload),
        timeout=60  # seconds
    )

    # DEBUG LOG
    print(f"Response Code: {response.status_code}")

    if response.status_code == 200:
        try:
            result = response.json()
            corrected = result["choices"][0]["message"]["content"].strip()

            corrected_filename = os.path.join(
                os.path.dirname(TRANSCRIPT_PATH),
                "corrected_" + os.path.basename(TRANSCRIPT_PATH)
            )

            with open(corrected_filename, "w", encoding="utf-8") as f:
                f.write(corrected)

            print(f"\n✅ Corrected transcript saved to:\n{corrected_filename}\n")
        except (json.JSONDecodeError, KeyError) as e:
            print("❌ Failed to parse model response.")
            print("Raw response:\n", response.text)
    else:
        print(f"❌ API Error {response.status_code}:")
        print(response.text)

except requests.exceptions.RequestException as e:
    print("❌ Network/API error occurred:")
    print(str(e))
