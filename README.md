# Elite Dangerous Downloader

## DISCLAIMER: 
This ReadMe and most of the Code is generated through Co-Pilot and then refactored/refined by the author. 

## Description
The Elite Dangerous Downloader is a Python-based application that allows users to download and verify files from a manifest URL. The app uses a Tkinter GUI for user-friendly interaction and supports pause, resume, and stop functionalities.

## Features
- **Manifest URL Input:** Prefilled URL for convenience.
- **Output Directory Selection:** Allows users to browse and select the output directory.
- **Progress Bar:** Shows download progress.
- **Pause/Resume:** Ability to pause and resume downloads.
- **Stop:** Stops the download process and closes the application.

## Installation
1. **Clone the repository:**
   ```sh
   git clone <repository-url>
   cd elite-dangerous-downloader
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

## Usage
1. **Run the application:**
   ```sh
   python EDDownload.py
   ```

2. **Input the manifest URL and select the output directory.**

3. **Click `Download` to start the download process.**

4. **Use `Pause` to pause the download, `Resume` to continue, and `Stop` to terminate the application.**

## Requirements
- Python 3.x
- Requests
- Tkinter

## Notes
- Ensure the output directory is empty before starting a new download to avoid overwriting existing files.
- The application verifies the integrity of downloaded files using SHA-1 hashes.

## License
This project is licensed under the MIT License.
```

Feel free to modify this further as needed! Let me know if there's anything else you'd like to add or change. 🚀
