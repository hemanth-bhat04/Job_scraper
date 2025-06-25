import psycopg2
import requests
import time

# ====== CONFIG ======
VIDEO_ID = "982394038"
API_URL = "http://164.52.194.25:8006/chat"

# ====== Prompt Components ======
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

# ====== Fetch transcript segments ======
cursor.execute("""
    SELECT _offset, original_text
    FROM new_vimeo_master_m
    WHERE video_id = %s
    ORDER BY _offset;
""", (VIDEO_ID,))
segments = cursor.fetchall()
print(f"Fetched {len(segments)} segments for video_id {VIDEO_ID}")

# ====== Process and correct each segment ======
for offset, raw_text in segments:
    if not raw_text or raw_text.strip() == "":
        print(f"Skipping empty segment at offset {offset}")
        continue

    full_prompt = SYSTEM_PROMPT + "\n\n" + USER_PROMPT_TEMPLATE.format(raw_text.strip())

    try:
        response = requests.post(
            url=API_URL,
            json={"prompt": full_prompt},
            timeout=60
        )

        print(f"Offset {offset} → Status {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            corrected_raw = data.get("content", "").strip()

            # Remove 'output:' prefix if present
            if corrected_raw.lower().startswith("output:"):
                corrected = corrected_raw[len("output:"):].strip()
            else:
                corrected = corrected_raw

            # Update the DB column 'text' with corrected output
            cursor.execute(
                """
                UPDATE new_vimeo_master_m
                SET text = %s
                WHERE video_id = %s AND _offset = %s;
                """,
                (corrected, VIDEO_ID, offset)
            )
            conn.commit()
            print(f"Updated DB at offset {offset}")
            time.sleep(2) 

        else:
            print(f"API error at offset {offset}: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Exception at offset {offset}: {str(e)}")

# ====== Clean up ======
cursor.close()
conn.close()
print("\nDone — all segments corrected and updated into DB.")
