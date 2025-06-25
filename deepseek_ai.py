import psycopg2
import requests
import json
import time

# === DB Connection ===
adhoc_db = psycopg2.connect(
    dbname="piruby_automation",
    user="postgres",
    password="piruby@157",
    host="164.52.194.25",
    port="5432"
)
adhoc_cursor = adhoc_db.cursor()

video = "981861307"

# === Step 1: Fetch per-minute transcript segments
adhoc_query3 = "SELECT _offset, text FROM new_vimeo_master_m WHERE video_id = %s ORDER BY _offset"
adhoc_cursor.execute(adhoc_query3, (video,))
per_min_texts = adhoc_cursor.fetchall()

# === Step 2: Create 5-minute chunks
five_min_chunks = [
    (per_min_texts[i][0], per_min_texts[i:i + 5])
    for i in range(0, len(per_min_texts), 5)
    if len(per_min_texts[i:i + 5]) == 5
]

# === Step 3: Process and print extracted keywords
for offset, chunk in five_min_chunks:
    five_min_text = " ".join([row[1].strip() for row in chunk if row[1]])

    if not five_min_text.strip():
        print(f"⏩ Skipping empty chunk at offset {offset}")
        continue

    prompt = (
        "Extract all domain-specific keywords and important technical terms from the following transcript. "
        "Include technical nouns, phrases, concepts, methods, and tools. "
        "Exclude filler, common verbs, English stopwords, names, math symbols, and explanations. "
        "Return only a comma-separated list of clean keywords or phrases.\n\n"
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
            keywords = result['choices'][0]['message']['content'].strip()
            print(f"\n🧠 Offset {offset} Keywords:\n{keywords}\n{'-'*60}")
            time.sleep(2)

        else:
            print(f"❌ API Error at offset {offset}: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"💥 Exception at offset {offset}: {str(e)}")

# === Cleanup
adhoc_cursor.close()
adhoc_db.close()
print("🏁 Done — All keywords printed.")
