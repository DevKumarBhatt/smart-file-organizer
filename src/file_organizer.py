
import shutil
import hashlib
import csv
import logging
from pathlib import Path

SOURCE_DIR = Path("sample_files")
OUTPUT_DIR = Path("organized_files")
REPORT_DIR = Path("reports")

FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx"],
    "Others": []
}


def setup_logging():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=REPORT_DIR / "organizer.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8",
        force=True
    )


def calculate_hash(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def format_size(size):
    if size < 1024:
        return f"{size} Bytes"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    else:
        return f"{size / (1024 * 1024):.2f} MB"


def get_category(file):
    extension = file.suffix.lower()

    for category, extensions in FILE_CATEGORIES.items():
        if extension in extensions:
            return category

    return "Others"


def organize_files():

    if not SOURCE_DIR.exists():
        print("Source folder does not exist!")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    setup_logging()

    files = [f for f in SOURCE_DIR.iterdir() if f.is_file()]

    if not files:
        print("No files found!")
        logging.warning("No files found in source folder.")
        return

    seen_hashes = {}
    duplicate_files = []
    file_sizes = []
    csv_records = []

    logging.info("File organization started.")

    for file in files:

        try:
            file_hash = calculate_hash(file)
            file_size = file.stat().st_size
            category = get_category(file)

            is_duplicate = file_hash in seen_hashes

            file_sizes.append((file.name, file_size))

            if is_duplicate:
                original = seen_hashes[file_hash]
                duplicate_files.append((file.name, original))

                logging.info(
                    "Duplicate found: %s | Original: %s",
                    file.name, original
                )

                print(f"Duplicate found: {file.name}")

            else:
                seen_hashes[file_hash] = file.name

                category_folder = OUTPUT_DIR / category
                category_folder.mkdir(parents=True, exist_ok=True)

                destination = category_folder / file.name
                shutil.copy2(file, destination)

                logging.info(
                    "Copied %s to %s",
                    file.name, category
                )

                print(f"Copied: {file.name} -> {category}")

            csv_records.append({
                "File Name": file.name,
                "Extension": file.suffix.lower(),
                "Category": category,
                "Size (Bytes)": file_size,
                "Size (Readable)": format_size(file_size),
                "Duplicate": "Yes" if is_duplicate else "No"
            })

        except (OSError, PermissionError) as error:
            logging.exception("Could not process file: %s", file.name)
            print(f"Error processing {file.name}: {error}")

    # Duplicate report
    with open(REPORT_DIR / "duplicate_report.txt", "w",
              encoding="utf-8") as report:

        report.write("DUPLICATE FILE DETECTION REPORT\n")
        report.write("=" * 35 + "\n\n")

        if duplicate_files:
            for duplicate, original in duplicate_files:
                report.write(
                    f"Duplicate: {duplicate} | Original: {original}\n"
                )
        else:
            report.write("No duplicate files found.\n")

    # File size report
    with open(REPORT_DIR / "file_size_report.txt", "w",
              encoding="utf-8") as report:

        report.write("FILE SIZE REPORT\n")
        report.write("=" * 35 + "\n\n")

        for name, size in file_sizes:
            report.write(f"{name} : {format_size(size)}\n")

    # CSV report
    csv_file = REPORT_DIR / "file_organization_report.csv"

    with open(csv_file, "w", newline="", encoding="utf-8-sig") as report:

        fieldnames = [
            "File Name",
            "Extension",
            "Category",
            "Size (Bytes)",
            "Size (Readable)",
            "Duplicate"
        ]

        writer = csv.DictWriter(report, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_records)

    logging.info(
        "Organization completed. Total: %d, Unique: %d, Duplicates: %d",
        len(files), len(seen_hashes), len(duplicate_files)
    )

    print("\nFile organization completed!")
    print(f"Total files checked: {len(files)}")
    print(f"Unique files: {len(seen_hashes)}")
    print(f"Duplicate files: {len(duplicate_files)}")
    print(f"CSV report saved: {csv_file}")
    print("Log file saved: reports/organizer.log")


if __name__ == "__main__":
    try:
        organize_files()
    except Exception:
        logging.exception("Unexpected application error.")
        print("An unexpected error occurred. Check the log file.")
