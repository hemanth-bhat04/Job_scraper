import psycopg2
import os

def fetch_all_video_segments(video_id: str, output_folder: str = "video_segments"):
    # Connect to the database
    conn = psycopg2.connect(
        dbname="piruby_automation",
        user="postgres",
        host="164.52.194.25",
        password="piruby@157",
        port="5432"
    )
    cursor = conn.cursor()

    # Query to fetch all 5-minute segments ordered by _offset
    query = "SELECT text FROM new_vimeo_master_m WHERE video_id = %s"
    cursor.execute(query, (video_id,))
    rows = cursor.fetchall()

    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Write each segment to a separate file
    for i, row in enumerate(rows):
        text = row[0]
        if text:
            file_path = os.path.join(output_folder, f"segment_{i}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text.strip() + "\n")
            print(f"Saved: {file_path}")

    cursor.close()
    conn.close()
    print(f"\n✅ Saved {len(rows)} transcript segments to folder: {output_folder}")

if __name__ == "__main__":
    video_id = "1001522042"
    fetch_all_video_segments(video_id)
