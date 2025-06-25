import psycopg2

# === DB Connection ===
conn = psycopg2.connect(
    dbname="piruby_automation",
    user="postgres",
    password="piruby@157",
    host="164.52.194.25",
    port="5432"
)
cursor = conn.cursor()

# === MANUAL INPUT ===
video_id = "982394038"  # 👈 Replace with any video ID you want to check

# === Fetch offsets and keywords for that video ===
query = """
    SELECT _offset, critical_keywords
    FROM new_vimeo_master_m
    WHERE video_id = %s
    ORDER BY _offset;
"""
cursor.execute(query, (video_id,))
results = cursor.fetchall()

# === Group and print in 5-minute chunks ===
print(f"\n🎥 Video ID: {video_id}")
print("=" * 60)

for i in range(0, len(results), 5):
    chunk = results[i:i + 5]
    if len(chunk) < 5:
        continue  # Skip incomplete chunks

    offset, keywords = chunk[0]
    print(f"🕒 Offset {offset} — Keywords:")
    print(keywords if keywords else "[Empty or missing]")
    print("-" * 60)

cursor.close()
conn.close()
