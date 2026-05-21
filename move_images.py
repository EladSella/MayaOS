import os
import glob
import shutil

src_dir = r"C:\Users\Elad\.gemini\antigravity\brain\80f37fe6-6896-4323-97e9-a26bc9ae5e93"
dst_dir = r"C:\Users\Elad\Documents\MayaOS\ui\assets"

agents = [
    "maya", "dr_liam", "gabriel", "dana", "mia", "lian", "leo",
    "ella", "chen", "daniel", "ron", "amir", "michal", "gil"
]

for agent in agents:
    pattern = os.path.join(src_dir, f"agent_{agent}_*.png")
    matches = glob.glob(pattern)
    if matches:
        # Get the latest one if multiple
        latest = max(matches, key=os.path.getctime)
        dst_path = os.path.join(dst_dir, f"agent_{agent}.png")
        shutil.copy2(latest, dst_path)
        print(f"Copied {latest} to {dst_path}")
    else:
        print(f"No match for {agent}")
