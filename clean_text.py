import requests
import json
import os

# ====== CONFIG ======
TRANSCRIPT_PATH = "D:/Job scraper/Job_scraper/video_segments/segment_1.txt"  # Your 1-min transcript file
API_KEY = "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"  # Replace with your OpenRouter API key
MODEL = "deepseek/deepseek-r1-0528:free"

# ====== LOAD RAW TRANSCRIPT ======
with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
    raw_text = f.read().strip()

# ====== PREPARE PROMPT ======
prompt = (
    "You are an expert language editor for technical transcripts. "
    "Correct the grammar, punctuation, sentence flow, and casing in the following transcript. "
    "Do not change or expand any technical terms, acronyms, or numeric values. "
    "Return only the corrected transcript text. Do not include any explanations, notes, or introductory phrases.\n\n"
    f"{raw_text}"
)

# ====== SEND REQUEST TO OPENROUTER ======
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://yourprojectdomain.com",  # Optional
    "X-Title": "TranscriptCleaner",                   # Optional
}

payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "system",
            "content": "You are a strict grammar editor for technical transcripts. Output only the corrected text—no explanations, no headings, no filler."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
}

response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    data=json.dumps(payload)
)

# ====== HANDLE RESPONSE ======
if response.status_code == 200:
    result = response.json()
    corrected = result["choices"][0]["message"]["content"].strip()

    # Build clean filename in same folder
    corrected_filename = os.path.join(
        os.path.dirname(TRANSCRIPT_PATH),
        "corrected_" + os.path.basename(TRANSCRIPT_PATH)
    )

    with open(corrected_filename, "w", encoding="utf-8") as f:
        f.write(corrected)

    print(f"\n✅ Corrected transcript saved to:\n{corrected_filename}\n")
else:
    print("❌ Error:", response.status_code)
    print(response.text)
