import os
import shutil
import json

BASE_CHANNELS_DIR = "channels"

def ensure_channels_dir():
    if not os.path.exists(BASE_CHANNELS_DIR):
        os.makedirs(BASE_CHANNELS_DIR)

def get_channel_structure():
    """
    Returns a dictionary: {'CategoryName': ['Channel1', 'Channel2'], ...}
    """
    ensure_channels_dir()
    structure = {}
    
    # List all categories (folders in channels/)
    categories = [
        d for d in os.listdir(BASE_CHANNELS_DIR) 
        if os.path.isdir(os.path.join(BASE_CHANNELS_DIR, d))
    ]
    
    for cat in categories:
        cat_path = os.path.join(BASE_CHANNELS_DIR, cat)
        channels = [
            c for c in os.listdir(cat_path)
            if os.path.isdir(os.path.join(cat_path, c))
        ]
        structure[cat] = channels
        
    return structure

def create_category(category_name):
    ensure_channels_dir()
    path = os.path.join(BASE_CHANNELS_DIR, category_name)
    if os.path.exists(path):
        raise FileExistsError(f"Kategori '{category_name}' sudah ada.")
    os.makedirs(path)
    return path

def create_new_channel(category_name, channel_name, source_client_secret):
    ensure_channels_dir()
    # Path: channels/Category/ChannelName
    cat_path = os.path.join(BASE_CHANNELS_DIR, category_name)
    if not os.path.exists(cat_path):
        os.makedirs(cat_path) # Auto create category if missing
        
    channel_path = os.path.join(cat_path, channel_name)
    
    if os.path.exists(channel_path):
        raise FileExistsError(f"Channel '{channel_name}' sudah ada di kategori '{category_name}'.")
    
    os.makedirs(channel_path)
    os.makedirs(os.path.join(channel_path, "uploads"), exist_ok=True)
    
    dest_secret = os.path.join(channel_path, "client_secret.json")
    shutil.copy(source_client_secret, dest_secret)
    
    config = {"daily_limit": 5, "privacy_default": "unlisted"}
    with open(os.path.join(channel_path, "config.json"), "w") as f:
        json.dump(config, f)
        
    return channel_path

def rename_channel_folder(category, old_name, new_name):
    base = os.path.join(BASE_CHANNELS_DIR, category)
    old_path = os.path.join(base, old_name)
    new_path = os.path.join(base, new_name)
    
    if not os.path.exists(old_path):
        raise FileNotFoundError("Channel lama tidak ditemukan.")
    if os.path.exists(new_path):
        raise FileExistsError("Nama channel sudah digunakan.")
        
    os.rename(old_path, new_path)
    return new_path

def delete_channel_folder(category, channel_name):
    path = os.path.join(BASE_CHANNELS_DIR, category, channel_name)
    if os.path.exists(path):
        shutil.rmtree(path)
    else:
        raise FileNotFoundError("Channel tidak ditemukan.")

# Optional: Rename/Delete Category
def delete_category_folder(category):
    path = os.path.join(BASE_CHANNELS_DIR, category)
    if os.path.exists(path):
        shutil.rmtree(path)
        
        # [TAMBAHKAN INI DI BAGIAN BAWAH utils.py]

def rename_category_folder(old_name, new_name):
    old_path = os.path.join(BASE_CHANNELS_DIR, old_name)
    new_path = os.path.join(BASE_CHANNELS_DIR, new_name)
    
    if not os.path.exists(old_path):
        raise FileNotFoundError("Kategori lama tidak ditemukan.")
    if os.path.exists(new_path):
        raise FileExistsError("Nama kategori sudah digunakan.")
        
    os.rename(old_path, new_path)
    return new_path