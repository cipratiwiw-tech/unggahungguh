import os
import shutil
import json

BASE_CHANNELS_DIR = "channels"

def ensure_channels_dir():
    if not os.path.exists(BASE_CHANNELS_DIR):
        os.makedirs(BASE_CHANNELS_DIR)

def get_existing_channels():
    ensure_channels_dir()
    return [
        d for d in os.listdir(BASE_CHANNELS_DIR) 
        if os.path.isdir(os.path.join(BASE_CHANNELS_DIR, d))
    ]

def create_new_channel(channel_name, source_client_secret):
    ensure_channels_dir()
    channel_path = os.path.join(BASE_CHANNELS_DIR, channel_name)
    
    if os.path.exists(channel_path):
        raise FileExistsError(f"Channel '{channel_name}' sudah ada.")
    
    os.makedirs(channel_path)
    os.makedirs(os.path.join(channel_path, "uploads"), exist_ok=True)
    
    dest_secret = os.path.join(channel_path, "client_secret.json")
    shutil.copy(source_client_secret, dest_secret)
    
    config = {"daily_limit": 5, "privacy_default": "unlisted"}
    with open(os.path.join(channel_path, "config.json"), "w") as f:
        json.dump(config, f)
        
    return channel_path

# --- FUNGSI RENAME (WAJIB ADA) ---
def rename_channel_folder(old_name, new_name):
    """
    Mengubah nama folder channel di disk.
    """
    old_path = os.path.join(BASE_CHANNELS_DIR, old_name)
    new_path = os.path.join(BASE_CHANNELS_DIR, new_name)
    
    if not os.path.exists(old_path):
        raise FileNotFoundError(f"Channel lama '{old_name}' tidak ditemukan di disk.")
    
    if os.path.exists(new_path):
        raise FileExistsError(f"Nama channel '{new_name}' sudah digunakan.")
        
    os.rename(old_path, new_path)
    return new_path

def delete_channel_folder(channel_name):
    channel_path = os.path.join(BASE_CHANNELS_DIR, channel_name)
    if os.path.exists(channel_path):
        shutil.rmtree(channel_path)
    else:
        raise FileNotFoundError(f"Channel '{channel_name}' tidak ditemukan.")