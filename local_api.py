import psycopg2
import requests
import os

# ====== CONFIG ======
VIDEO_ID = "981861307"
API_URL = "http://164.52.194.25:8006/chat"
OUTPUT_DIR = "corrected_segments"

# ====== Ensure output directory exists ======
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ====== Strong grammar correction prompt ======
SYSTEM_PROMPT = (
    "You are a strict grammar correction engine. "
    "Fix only grammar, punctuation, and sentence structure. "
    "Do not change acronyms, technical terms, or numbers. "
    "Return ONLY the corrected transcript — no explanations, no headings, no notes."
)

USER_PROMPT_TEMPLATE = (
    "Correct the following transcript text. "
    "Fix only grammar, punctuation, and sentence flow. "
    "Do not touch acronyms, numbers, or domain-specific words. "
    "Return only the corrected version. Do not say 'Here is the corrected text' or anything else.\n\n{}"
)

# ====== Connect to PostgreSQL ======
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

    full_prompt = SYSTEM_PROMPT + "\n\n" + USER_PROMPT_TEMPLATE.format(raw_text.strip())

    try:
        response = requests.post(
            url=API_URL,
            json={"prompt": full_prompt},
            timeout=60
        )

        print(f"📡 Offset {offset} → Status {response.status_code}")

        if response.status_code == 200:
            # Extract the response content
            data = response.json()
            corrected_raw = data.get("content", "").strip()

            # Remove leading "output:" or similar prefix
            if corrected_raw.lower().startswith("output:"):
                corrected = corrected_raw[len("output:"):].strip()
            else:
                corrected = corrected_raw

            # Save corrected output
            filename = os.path.join(OUTPUT_DIR, f"corrected_segment_{offset}.txt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(corrected)

            print(f"✅ Saved: {filename}")
        else:
            print(f"❌ API error at offset {offset}: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"💥 Exception at offset {offset}: {str(e)}")

# ====== Cleanup ======
cursor.close()
conn.close()
print("\n🏁 Done — all segments processed using local model.")
