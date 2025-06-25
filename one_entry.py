import psycopg2
import requests
import time

# ====== CONFIG ======
VIDEO_ID = "981861307"
TEST_OFFSET = 60  # ← Change this to test a different offset
API_URL = "http://164.52.194.25:8006/chat"

# ====== Prompt Setup ======
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

# ====== Fetch one specific entry ======
cursor.execute("""
    SELECT _offset, original_text
    FROM new_vimeo_master_m
    WHERE video_id = %s AND _offset = %s;
""", (VIDEO_ID, TEST_OFFSET))

segment = cursor.fetchone()

if segment:
    offset, raw_text = segment
    if not raw_text or raw_text.strip() == "":
        print(f"⚠️ Skipping empty segment at offset {offset}")
    else:
        full_prompt = SYSTEM_PROMPT + "\n\n" + USER_PROMPT_TEMPLATE.format(raw_text.strip())

        try:
            response = requests.post(
                url=API_URL,
                json={"prompt": full_prompt},
                timeout=60
            )

            print(f"📡 API response for offset {offset} → Status {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                corrected_raw = data.get("content", "").strip()

                # Remove 'output:' prefix if present
                if corrected_raw.lower().startswith("output:"):
                    corrected = corrected_raw[len("output:"):].strip()
                else:
                    corrected = corrected_raw

                # ✅ Update DB
                cursor.execute("""
                    UPDATE new_vimeo_master_m
                    SET text = %s
                    WHERE video_id = %s AND _offset = %s;
                """, (corrected, VIDEO_ID, offset))
                conn.commit()

                print(f"✅ DB updated for offset {offset}")
                time.sleep(5)

            else:
                print(f"❌ API error: {response.status_code}")
                print(response.text)

        except Exception as e:
            print(f"💥 Exception occurred: {str(e)}")

else:
    print(f"❌ No entry found for video_id {VIDEO_ID} with offset {TEST_OFFSET}")

# ====== Cleanup ======
cursor.close()
conn.close()
print("🏁 Done (one entry).")
