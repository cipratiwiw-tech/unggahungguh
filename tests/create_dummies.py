import os
import json

def create_dummies():
    # 1. Buat folder assets dummy
    base_dir = "test_assets"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        print(f"[OK] Folder '{base_dir}' dibuat.")

    # 2. Buat Dummy Video Files (0 KB tapi ekstensi .mp4)
    video_names = ["video_test_1.mp4", "video_shorts_2.mp4", "tutorial_py.mkv"]
    for v in video_names:
        path = os.path.join(base_dir, v)
        with open(path, "w") as f:
            f.write("DUMMY VIDEO CONTENT")
        print(f"[OK] Dummy video dibuat: {path}")

    # 3. Buat Dummy Client Secret (JSON)
    secret_path = os.path.join(base_dir, "dummy_client_secret.json")
    dummy_secret = {
        "installed": {
            "client_id": "dummy_id",
            "client_secret": "dummy_secret",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }
    with open(secret_path, "w") as f:
        json.dump(dummy_secret, f, indent=2)
    print(f"[OK] Dummy secret dibuat: {secret_path}")
    
    # 4. Buat Dummy Thumbnail
    thumb_path = os.path.join(base_dir, "thumb.jpg")
    # Buat file kosong saja, Qt mungkin tidak bisa render tapi tidak akan error fatal
    with open(thumb_path, "wb") as f:
        f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF') # Header JPG minimal
    print(f"[OK] Dummy thumbnail dibuat: {thumb_path}")

if __name__ == "__main__":
    create_dummies()
    print("\n--- SIAP DITES ---")
    print("Gunakan file di folder 'test_assets' untuk drag-and-drop ke aplikasi.")