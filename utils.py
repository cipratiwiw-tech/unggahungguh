import os
import json

def create_structure(project_name, channel_name):
    """Membuat struktur folder sesuai schema final."""
    base_path = os.path.join("projects", project_name, "channels", channel_name)
    folders = ["uploads", "metadata", "thumbnails"]
    
    for folder in folders:
        os.makedirs(os.path.join(base_path, folder), exist_ok=True)
    
    return base_path

def get_token_path(project_name, channel_name):
    return os.path.join("projects", project_name, "channels", channel_name, "token.json")

def get_client_secret_path(project_name):
    # Asumsi client_secret.json ada di root folder project_A
    return os.path.join("projects", project_name, "client_secret.json")