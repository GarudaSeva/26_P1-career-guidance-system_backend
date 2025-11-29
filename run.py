import pandas as pd

def main():
    file_path = "data/career_data_processed.csv"

    try:
        # Load CSV file
        df = pd.read_csv(file_path)

        # Check if job_title column exists
        if "job_title" not in df.columns:
            print("❌ 'job_title' column not found in CSV file.")
            return

        # Print job titles
        print("📌 Job Titles List:\n")
        for title in df["job_title"]:
            print(title)

        # Print total count
        print("\n==============================")
        print("🔢 Total Job Titles:", len(df["job_title"]))
        print("==============================")

    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
