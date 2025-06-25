import psycopg2

# ====== DB Config ======
conn = psycopg2.connect(
    dbname="piruby_automation",
    user="postgres",
    password="piruby@157",
    host="164.52.194.25",
    port="5432"
)

cursor = conn.cursor()

# ====== Set video_id ======
video_id = ""  # <-- replace with your actual video_id

# ====== Fetch text for that video ======
query = """
    SELECT _offset, original_text, text, critical_keywords
    FROM new_vimeo_master_m
    WHERE video_id = %s 
    ORDER BY _offset;
"""
cursor.execute(query, (video_id,))
results = cursor.fetchall()

# ====== Display ======
for offset, original_text, text, critical_keywords in results:
    print(f"Offset: {offset}\nText: {original_text}\n{'-'*50}, \nCorrected:{text}\n{'='*50}, \nKeywords: {critical_keywords}\n{'-'*50}\n")

cursor.close()
conn.close()
