import psycopg2
import requests
import json
import time

# === CONFIG ===
VIDEO_ID = "981861307"
START_INDEX = 0  # Set to 0, 5, 10, etc. for different 5-minute chunks

# === DB Connection ===
adhoc_db = psycopg2.connect(
    dbname="piruby_automation",
    user="postgres",
    password="piruby@157",
    host="164.52.194.25",
    port="5432"
)
adhoc_cursor = adhoc_db.cursor()

# === Fetch all per-minute texts ===
adhoc_cursor.execute(
    "SELECT _offset, text FROM new_vimeo_master_m WHERE video_id = %s ORDER BY _offset",
    (VIDEO_ID,)
)
per_min_texts = adhoc_cursor.fetchall()

# === Select only 5-minute chunk starting at START_INDEX
if len(per_min_texts) >= START_INDEX + 5:
    chunk = per_min_texts[START_INDEX:START_INDEX + 5]
    offset = chunk[0][0]  # Use the offset of the first minute in the 5-min block
    five_min_text = " ".join([row[1].strip() for row in chunk if row[1]])
else:
    print(f"❌ Not enough segments starting from index {START_INDEX}")
    exit()

# === Build keyword extraction prompt
prompt = (
    "Extract all domain-specific keywords and technical terms from the following transcript. "
    "Prioritize them by relevance to the content, putting the most important ones first. "
    "Include only meaningful terms related to methods, tools, concepts, or domain-specific language. "
    "Strictly exclude filler words, common English, verbs, names, math symbols, and explanations. "
    "Return only a comma-separated list of keywords or phrases in order of importance.\n\n"
    + five_min_text
)

try:
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer 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",
            "Content-Type": "application/json"
        },
        data=json.dumps({
            "model": "deepseek/deepseek-r1-0528:free",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }),
        timeout=60
    )

    if response.status_code == 200:
        result = response.json()
        keywords_text = result['choices'][0]['message']['content'].strip()

        # === Convert to PostgreSQL array format: '{item1,item2,...}'
        keyword_list = [kw.strip() for kw in keywords_text.split(",") if kw.strip()]
        keywords_array = "{" + ",".join(keyword_list) + "}"

        # === Update DB
        update_query = """
            UPDATE new_vimeo_master_m
            SET critical_keywords = %s
            WHERE video_id = %s AND _offset = %s;
        """
        adhoc_cursor.execute(update_query, (keywords_array, VIDEO_ID, offset))
        adhoc_db.commit()

        print(f"✅ Offset {offset} updated with keywords:\n{keywords_array}")

    else:
        print(f"❌ API Error: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"💥 Exception occurred: {str(e)}")

# === Cleanup
adhoc_cursor.close()
adhoc_db.close()
print("🏁 Done — One 5-minute entry tested and updated.")
