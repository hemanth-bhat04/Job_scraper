import psycopg2
import requests
import json
import time
import socket
from requests.exceptions import ConnectionError

# === CONFIG ===
VIDEO_ID = "982394038"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = "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"
MAX_RETRIES = 2

# === DB Connection ===
adhoc_db = psycopg2.connect(
    dbname="piruby_automation",
    user="postgres",
    password="piruby@157",
    host="164.52.194.25",
    port="5432"
)
adhoc_cursor = adhoc_db.cursor()

# === Fetch all per-minute texts for video ===
adhoc_cursor.execute(
    "SELECT _offset, text FROM new_vimeo_master_m WHERE video_id = %s ORDER BY _offset",
    (VIDEO_ID,)
)
per_min_texts = adhoc_cursor.fetchall()

# === Filter: Start only from offset >= 1800
per_min_texts = [(o, t) for o, t in per_min_texts if o >= 7800]


# === Create 5-minute chunks ===
five_min_chunks = [
    (per_min_texts[i][0], per_min_texts[i:i + 5])
    for i in range(0, len(per_min_texts), 5)
    if len(per_min_texts[i:i + 5]) == 5
]

# === Helper: call OpenRouter API with retries ===
def get_keywords_from_api(prompt):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(
                url=API_URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": "deepseek/deepseek-r1-0528:free",
                    "messages": [{"role": "user", "content": prompt}]
                }),
                timeout=60
            )

            if response.status_code == 200:
                return response.json()

            else:
                print(f"❌ API Error (attempt {attempt}): {response.status_code}")
                print(response.text)

        except (ConnectionError, socket.error, socket.timeout) as e:
            print(f"⚠️ Network issue (attempt {attempt}): {e}")

        time.sleep(3)

    return None  # all retries failed

# === Process and update each 5-minute chunk ===
for offset, chunk in five_min_chunks:
    five_min_text = " ".join([row[1].strip() for row in chunk if row[1]])

    if not five_min_text.strip():
        print(f"⏩ Skipping empty chunk at offset {offset}")
        continue

    prompt = (
        "Extract all domain-specific keywords and technical terms from the following transcript. "
        "Prioritize them by relevance to the content, putting the most important ones first. "
        "Include only meaningful terms related to methods, tools, concepts, or domain-specific language. "
        "Strictly exclude filler words, common English, verbs, names, math symbols, and explanations. "
        "Return only a comma-separated list of keywords or phrases in order of importance.\n\n"
        + five_min_text[:3000]  # limit size for stability
    )

    result = get_keywords_from_api(prompt)

    if not result or "choices" not in result:
        print(f"❌ Skipping offset {offset} due to failed retries.")
        continue

    keywords_text = result['choices'][0]['message']['content'].strip()
    first_line = keywords_text.split("\n")[0].strip()
    keyword_list = [kw.strip() for kw in first_line.split(",") if kw.strip()]
    keywords_array = "{" + ",".join(keyword_list) + "}"

    try:
        # === Update DB
        update_query = """
            UPDATE new_vimeo_master_m
            SET critical_keywords = %s
            WHERE video_id = %s AND _offset = %s;
        """
        adhoc_cursor.execute(update_query, (keywords_array, VIDEO_ID, offset))
        adhoc_db.commit()

        print(f"✅ Offset {offset} updated with keywords: {keywords_array}")
        time.sleep(2)

    except Exception as e:
        print(f"💥 DB error at offset {offset}: {e}")

# === Cleanup
adhoc_cursor.close()
adhoc_db.close()
print("🏁 Done — All segments processed with retries.")
