import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import xml.etree.ElementTree as ET
import requests
import os
import gzip
import io
import threading
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

LIVE_MANIFEST = "http://cdn.zaonce.net/elitedangerous/win/manifests/Win64_4_0_0_Update19_CobraV_Final_CLEAN+%282024.12.10.308767%29.xml.gz"

# Threading events for pausing and stopping
pause_event = threading.Event()
stop_event = threading.Event()

def download_and_verify(url, path, expected_hash):
    if download_file(url, path):
        if verify_file(path, expected_hash):
            return path
    return None

def download_file(url, path):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if stop_event.is_set():
                        return False

                    # Check for pause event
                    pause_event.wait()

                    f.write(chunk)
            print(f"Downloaded {path}")
            return True
        else:
            print(f"Failed to download {url}")
            return False
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def verify_file(path, expected_hash):
    sha1 = hashlib.sha1()
    try:
        with open(path, 'rb') as f:
            while chunk := f.read(8192):
                sha1.update(chunk)
        file_hash = sha1.hexdigest()
        return file_hash == expected_hash
    except Exception as e:
        print(f"Error verifying file {path}: {e}")
        return False

def parse_manifest(tree_root, output_dir, download_futures):
    try:
        with ThreadPoolExecutor(max_workers=16) as executor:  # Adjust the number of workers as needed    
            for file in tree_root.findall('File'):
                # Check for stop event
                if stop_event.is_set():
                    return

                # Check for pause event
                pause_event.wait()

                path = os.path.join(output_dir, file.find('Path').text)
                url = file.find('Download').text
                expected_hash = file.find('Hash').text

                # Create directories if they don't exist
                os.makedirs(os.path.dirname(path), exist_ok=True)

                # Submit download tasks to the thread pool
                download_futures.append(executor.submit(download_and_verify, url, path, expected_hash))
    except Exception as e:
        print(f"Error processing manifest: {e}")
        download_button.config(state=tk.NORMAL)
        pause_resume_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.DISABLED)
    

def start_download():
    global tree_root, download_futures
    url = url_entry.get()
    output_dir = output_dir_entry.get()
    # Validate inputs
    if not url or not output_dir:
        messagebox.showerror("Error", "Please provide both the manifest URL and the output directory.")
        return

    # Input validation
    if not os.path.isdir(output_dir):
        messagebox.showerror("Error", "The output directory is not valid.")
        return

    # Check if the directory is not empty
    if os.listdir(output_dir):
        result = messagebox.askyesno("Warning", "The output directory is not empty. Do you want to continue?")
        if not result:
            download_button.config(state=tk.NORMAL)
            return

    # Disable the download button to prevent starting multiple downloads
    download_button.config(state=tk.DISABLED)
    pause_resume_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.NORMAL)

    # Get Manifest File
    response = requests.get(url)
    if response.status_code == 200:
        # Decompress the .gz file
        with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz:
            xml_content = gz.read()
            tree_root = ET.fromstring(xml_content)
    else:
        print(f"Failed to download manifest from {url}")
        download_button.config(state=tk.NORMAL)
        pause_resume_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.DISABLED)
    
    # Reset the pause and stop events
    pause_event.set()
    stop_event.clear()

    # Set progress bar limits.
    total_files = len(tree_root.findall('File'))
    progress_bar.configure(maximum=total_files)

    download_futures = []

    # Create Thread that handles downloads
    download_thread = threading.Thread(target=parse_manifest, args=(tree_root, output_dir, download_futures))
    download_thread.start()

    # Run progress updates in a separate thread 
    root.after(100, update_progress, download_futures, total_files) 

def toggle_pause_resume():
    if pause_event.is_set():
        pause_event.clear()
        pause_resume_button.config(text="Resume")
    else:
        pause_event.set()
        pause_resume_button.config(text="Pause")

def stop_download():
    stop_event.set()
    # Allow time for threads to terminate
    for future in download_futures:
        future.cancel()  # Attempt to cancel running futures

    # Terminate the Tkinter event loop after a slight delay
    root.after(500, root.quit)


def update_progress(futures, total_files, downloaded_files=0):
    try:
        for future in futures:
            if future.done():
                result = future.result()
                if result:
                    downloaded_files += 1
                    futures.remove(future)

        progress_var.set(downloaded_files)
        progress_label.config(text=f"{downloaded_files}/{total_files} files downloaded")
        progress_bar.update_idletasks()

        if downloaded_files < total_files:
            root.after(100, update_progress, futures, total_files, downloaded_files)
        else:
            # Re-enable buttons once completed
            download_button.config(state=tk.NORMAL)
            pause_resume_button.config(state=tk.DISABLED)
            stop_button.config(state=tk.DISABLED)
    except Exception as e:
        print(f"Error updating progress: {e}")
        download_button.config(state=tk.NORMAL)
        pause_resume_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.DISABLED)

# Create the main window
root = tk.Tk()
root.title("Elite Dangerous Downloader")

# Make the window resizable
root.minsize(500,300)
root.columnconfigure(1, weight=1)
root.rowconfigure(2, weight=1)

# Manifest URL input
tk.Label(root, text="Manifest URL:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
url_entry = tk.Entry(root, width=50)
url_entry.insert(0, LIVE_MANIFEST)
url_entry.grid(row=0, column=1, padx=10, pady=5, sticky="we")

# Output directory selection
tk.Label(root, text="Output Directory:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
output_dir_entry = tk.Entry(root, width=50)
output_dir_entry.grid(row=1, column=1, padx=10, pady=5, sticky="we")

def select_output_dir():
    directory = filedialog.askdirectory()
    if directory:
        output_dir_entry.delete(0, tk.END)
        output_dir_entry.insert(0, directory)

tk.Button(root, text="Browse...", command=select_output_dir).grid(row=1, column=2, padx=5, pady=5)

# Progress bar and label
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var)
progress_bar.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="we")

progress_label = tk.Label(root, text="0/0 files downloaded")
progress_label.grid(row=3, column=0, columnspan=3, pady=5, sticky="we")

# Download button
download_button = tk.Button(root, text="Download", command=start_download)
download_button.grid(row=4, column=0, padx=5, pady=5, sticky="we")

# Pause/Resume button
pause_resume_button = tk.Button(root, text="Pause", command=toggle_pause_resume, state=tk.DISABLED)
pause_resume_button.grid(row=4, column=1, padx=5, pady=5, sticky="we")

# Stop Button
stop_button = tk.Button(root, text="Stop", command=stop_download, state=tk.DISABLED)
stop_button.grid(row=4, column=2, padx=5, pady=5, sticky="we")

# Run the application
root.mainloop()
