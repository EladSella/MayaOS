import time
import subprocess
import os
from datetime import datetime

def auto_git_sync():
    print("Auto Git Sync started. Will check for changes every 30 minutes.")
    while True:
        try:
            # Sleep first so it doesn't immediately push on startup
            time.sleep(1800)
            
            # Add all non-ignored files
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
            
            # Check if there are changes to commit (returns 1 if changes exist)
            result = subprocess.run(["git", "diff", "--staged", "--quiet"], capture_output=True)
            
            if result.returncode == 1:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_msg = f"Auto-sync backup: {timestamp}"
                
                subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
                subprocess.run(["git", "push", "origin", "main"], check=True, capture_output=True)
                print(f"[{timestamp}] Successfully pushed changes to GitHub.")
        except Exception as e:
            print(f"Error during auto sync: {e}")

if __name__ == "__main__":
    auto_git_sync()
