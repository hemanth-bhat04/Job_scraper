import psycopg2
import requests
import json
import os

# ====== CONFIG ======
VIDEO_ID = "981861307"
API_KEY = "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"
MODEL = "meta-llama/llama-3.1-8b-instruct:free"
OUTPUT_DIR = "corrected_segments"

# ====== Ensure output directory exists ======
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ====== Strong system prompt (unchanged) ======
system_message = (
    "You are a strict grammar correction engine. "
    "Fix only grammar, punctuation, and sentence structure. "
    "Do not change acronyms, technical terms, or numbers. "
    "Very strictly — return ONLY the corrected transcript — no explanations, no headings, no notes."
)

# ====== Connect to DB ======
conn = psycopg2.connect(
    dbname="piruby_automation",
    user="postgres",
    password="piruby@157",
    host="164.52.194.25",
    port="5432"
)
cursor = conn.cursor()

cursor.execute("""
    SELECT _offset, original_text
    FROM new_vimeo_master_m
    WHERE video_id = %s
    ORDER BY _offset;
""", (VIDEO_ID,))
segments = cursor.fetchall()
print(f"📥 Fetched {len(segments)} segments for video_id {VIDEO_ID}")

# ====== Process each transcript chunk ======
for offset, raw_text in segments:
    if not raw_text or raw_text.strip() == "":
        print(f"⏩ Skipping empty segment at offset {offset}")
        continue

    user_prompt = (
        "Correct the following transcript text. "
        "Fix only grammar, punctuation, and sentence flow. "
        "Do not touch acronyms, numbers, or domain-specific words."
        "Return only the corrected version. Do not say 'Here is the corrected text' or anything else.\n\n"
        + raw_text.strip()
    )

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

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=60
        )

        print(f"📡 Offset {offset} → Status {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            corrected = result["choices"][0]["message"]["content"].strip()

            filename = os.path.join(OUTPUT_DIR, f"corrected_segment_{offset}.txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(corrected)

            print(f"✅ Saved: {filename}")
        else:
            print(f"❌ Error at offset {offset}: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"💥 Exception at offset {offset}: {str(e)}")

# ====== Cleanup ======
cursor.close()
conn.close()
print("\n🏁 Done — All segments processed.")
