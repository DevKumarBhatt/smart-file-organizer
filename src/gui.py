
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import shutil
import hashlib
import csv
import logging
import os

selected_folder = None
csv_report_path = None


# ---------------- LOGGING ----------------

def setup_logging(report_folder):
    report_folder.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=report_folder / "organizer.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8",
        force=True
    )


# ---------------- FILE UTILITIES ----------------

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


# ---------------- GUI FUNCTIONS ----------------

def add_log(message):
    activity_log.config(state="normal")
    activity_log.insert(tk.END, message + "\n")
    activity_log.see(tk.END)
    activity_log.config(state="disabled")


def update_stats(total, organized, duplicates):
    total_value.config(text=str(total))
    organized_value.config(text=str(organized))
    duplicate_value.config(text=str(duplicates))


def select_folder():
    global selected_folder

    folder = filedialog.askdirectory(
        title="Select Folder to Organize"
    )

    if folder:
        selected_folder = Path(folder)

        folder_label.config(text=str(selected_folder))
        status_label.config(text="Folder selected successfully!")

        add_log(f"Selected folder: {selected_folder}")


def organize_files():
    global csv_report_path

    if selected_folder is None:
        messagebox.showwarning(
            "Warning",
            "Please select a folder first!"
        )
        return

    files = [
        file for file in selected_folder.iterdir()
        if file.is_file()
    ]

    if not files:
        messagebox.showinfo(
            "Information",
            "No files found in the selected folder."
        )
        return

    output_folder = selected_folder / "Organized_Files"
    report_folder = selected_folder / "Organizer_Reports"

    categories = {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
        "Documents": [".pdf", ".doc", ".docx", ".txt", ".xlsx"],
        "Others": []
    }

    output_folder.mkdir(exist_ok=True)
    report_folder.mkdir(exist_ok=True)

    setup_logging(report_folder)

    seen_hashes = {}
    duplicate_records = []
    csv_records = []

    organized = 0
    duplicates = 0
    errors = 0

    progress_bar["maximum"] = len(files)
    progress_bar["value"] = 0

    status_label.config(text="Organizing files...")
    organize_button.config(state="disabled")

    add_log("Starting file organization...")
    root.update_idletasks()

    for index, file in enumerate(files, start=1):

        try:
            file_hash = calculate_hash(file)
            file_size = file.stat().st_size

            category = "Others"

            for name, extensions in categories.items():
                if file.suffix.lower() in extensions:
                    category = name
                    break

            is_duplicate = file_hash in seen_hashes

            if is_duplicate:
                original = seen_hashes[file_hash]
                duplicate_records.append(
                    (file.name, original)
                )

                duplicates += 1

                add_log(f"Duplicate found: {file.name}")

                logging.info(
                    "Duplicate: %s | Original: %s",
                    file.name, original
                )

            else:
                seen_hashes[file_hash] = file.name

                category_folder = output_folder / category
                category_folder.mkdir(
                    parents=True,
                    exist_ok=True
                )

                destination = category_folder / file.name
                shutil.copy2(file, destination)

                organized += 1

                add_log(f"Organized: {file.name} -> {category}")

                logging.info(
                    "Copied %s to %s",
                    file.name, category
                )

            csv_records.append({
                "File Name": file.name,
                "Extension": file.suffix.lower(),
                "Category": category,
                "Size (Bytes)": file_size,
                "Size": format_size(file_size),
                "Duplicate": "Yes" if is_duplicate else "No"
            })

        except OSError as error:
            errors += 1
            add_log(f"Error: {file.name} - {error}")
            logging.exception("Could not process %s", file.name)

        progress_bar["value"] = index
        update_stats(index, organized, duplicates)
        root.update_idletasks()

    # Generate CSV report
    csv_report_path = report_folder / "file_organization_report.csv"

    with open(
        csv_report_path,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as report:

        fields = [
            "File Name",
            "Extension",
            "Category",
            "Size (Bytes)",
            "Size",
            "Duplicate"
        ]

        writer = csv.DictWriter(report, fieldnames=fields)
        writer.writeheader()
        writer.writerows(csv_records)

    # Generate duplicate report
    duplicate_report = report_folder / "duplicate_report.txt"

    with open(duplicate_report, "w", encoding="utf-8") as report:

        report.write("DUPLICATE FILE REPORT\n")
        report.write("=" * 35 + "\n\n")

        if duplicate_records:
            for duplicate, original in duplicate_records:
                report.write(
                    f"Duplicate: {duplicate} | Original: {original}\n"
                )
        else:
            report.write("No duplicate files found.\n")

    logging.info(
        "Completed: Total=%d, Organized=%d, Duplicates=%d, Errors=%d",
        len(files), organized, duplicates, errors
    )

    organize_button.config(state="normal")
    status_label.config(text="Organization completed!")

    add_log("Organization completed successfully!")
    add_log(f"Total files: {len(files)}")
    add_log(f"Errors: {errors}")

    messagebox.showinfo(
        "Organization Complete",
        f"Total Files: {len(files)}\n"
        f"Organized: {organized}\n"
        f"Duplicates: {duplicates}\n"
        f"Errors: {errors}\n\n"
        f"Reports saved in:\n{report_folder}"
    )


def open_report():
    if csv_report_path is None or not csv_report_path.exists():
        messagebox.showwarning(
            "Report Not Available",
            "Please organize files first."
        )
        return

    os.startfile(str(csv_report_path))


def clear_results():
    activity_log.config(state="normal")
    activity_log.delete("1.0", tk.END)
    activity_log.config(state="disabled")

    progress_bar["value"] = 0
    update_stats(0, 0, 0)

    status_label.config(text="Ready")


# ---------------- MAIN WINDOW ----------------

root = tk.Tk()
root.title("Smart File Organizer - Dashboard")
root.geometry("850x700")
root.configure(bg="#111827")
root.resizable(False, False)

# Heading
tk.Label(
    root,
    text="SMART FILE ORGANIZER",
    font=("Arial", 25, "bold"),
    bg="#111827",
    fg="white"
).pack(pady=(25, 5))

tk.Label(
    root,
    text="Intelligent File Management Dashboard",
    font=("Arial", 11),
    bg="#111827",
    fg="#9CA3AF"
).pack(pady=5)

# Statistics dashboard
stats_frame = tk.Frame(root, bg="#111827")
stats_frame.pack(fill="x", padx=30, pady=20)


def create_stat_card(parent, title, color):
    card = tk.Frame(parent, bg="#1F2937", padx=15, pady=15)

    tk.Label(
        card,
        text=title,
        font=("Arial", 11),
        bg="#1F2937",
        fg="#D1D5DB"
    ).pack()

    value = tk.Label(
        card,
        text="0",
        font=("Arial", 25, "bold"),
        bg="#1F2937",
        fg=color
    )
    value.pack(pady=8)

    return card, value


card1, total_value = create_stat_card(
    stats_frame, "Total Files", "#60A5FA"
)

card2, organized_value = create_stat_card(
    stats_frame, "Organized Files", "#34D399"
)

card3, duplicate_value = create_stat_card(
    stats_frame, "Duplicates", "#F87171"
)

card1.pack(side="left", expand=True, fill="x", padx=5)
card2.pack(side="left", expand=True, fill="x", padx=5)
card3.pack(side="left", expand=True, fill="x", padx=5)

# Folder selection
folder_frame = tk.Frame(root, bg="#1F2937", padx=15, pady=15)
folder_frame.pack(fill="x", padx=35, pady=10)

tk.Label(
    folder_frame,
    text="SELECTED FOLDER",
    font=("Arial", 10, "bold"),
    bg="#1F2937",
    fg="#60A5FA"
).pack(anchor="w")

folder_label = tk.Label(
    folder_frame,
    text="No folder selected",
    font=("Arial", 10),
    bg="#1F2937",
    fg="white",
    wraplength=730,
    justify="left"
)
folder_label.pack(anchor="w", pady=8)

# Buttons
button_frame = tk.Frame(root, bg="#111827")
button_frame.pack(pady=15)


def create_button(parent, text, command, color):
    return tk.Button(
        parent,
        text=text,
        command=command,
        font=("Arial", 10, "bold"),
        bg=color,
        fg="white",
        activebackground=color,
        activeforeground="white",
        relief="flat",
        padx=15,
        pady=12,
        cursor="hand2"
    )


create_button(
    button_frame, "SELECT FOLDER",
    select_folder, "#2563EB"
).pack(side="left", padx=6)

organize_button = create_button(
    button_frame, "ORGANIZE FILES",
    organize_files, "#16A34A"
)
organize_button.pack(side="left", padx=6)

create_button(
    button_frame, "OPEN CSV REPORT",
    open_report, "#7C3AED"
).pack(side="left", padx=6)

create_button(
    button_frame, "CLEAR",
    clear_results, "#475569"
).pack(side="left", padx=6)

# Progress bar
tk.Label(
    root,
    text="Processing Progress",
    font=("Arial", 10, "bold"),
    bg="#111827",
    fg="white"
).pack(anchor="w", padx=40, pady=(10, 5))

progress_bar = ttk.Progressbar(
    root,
    orient="horizontal",
    mode="determinate",
    length=770
)
progress_bar.pack(padx=40, pady=5)

# Activity log
tk.Label(
    root,
    text="ACTIVITY LOG",
    font=("Arial", 11, "bold"),
    bg="#111827",
    fg="white"
).pack(anchor="w", padx=40, pady=(15, 5))

activity_log = tk.Text(
    root,
    height=9,
    width=95,
    bg="#1F2937",
    fg="#D1D5DB",
    font=("Consolas", 9),
    relief="flat",
    padx=12,
    pady=10,
    state="disabled"
)
activity_log.pack(padx=35, pady=5)

# Status
status_label = tk.Label(
    root,
    text="Ready",
    font=("Arial", 10, "bold"),
    bg="#111827",
    fg="#34D399"
)
status_label.pack(pady=10)

root.mainloop()
