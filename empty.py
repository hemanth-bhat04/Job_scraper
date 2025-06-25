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

# === CONFIG ===
video_id = "982394038"
target_offset = 0

# === Update query ===
cursor.execute(
    """
    UPDATE new_vimeo_master_m
    SET critical_keywords = %s
    WHERE video_id = %s AND _offset = %s
    """,
    ("{}", video_id, target_offset)
)

conn.commit()
print(f"✅ Offset {target_offset} updated to empty keyword list.")

cursor.close()
conn.close()
