# src/scraper.py
import os
import yaml
from youtube_utils import get_channel_id_from_youtube


# --- Main Functions ---
def load_video_ids(yaml_dir: str):
    """Loads video IDs from a data YAML file."""
    data_path = os.path.join(yaml_dir, "video_ids.yaml")
    with open(data_path, 'r') as file:
        yaml_ids = yaml.safe_load(file)
    return yaml_ids.get("VIDEO_IDS_TO_SCRAPE", [])

def load_channel_info(yaml_dir: str):
    """Loads video IDs from a data YAML file."""
    data_path = os.path.join(yaml_dir, "channel_ids.yaml")
    with open(data_path, 'r') as file:
        yaml_ids = yaml.safe_load(file)
    return yaml_ids.get("CHANNEL_IDS", [])

def read_channel_names(yaml_path='yamls/channels.yaml'):
    """
    Reads channel names from a YAML file.

    Args:
        yaml_path (str): The path to the YAML file containing channel names.

    Returns:
        list: A list of channel names.
    """
    try:
        with open(yaml_path, 'r') as file:
            channels = yaml.safe_load(file)
            if isinstance(channels, dict) and 'CHANNEL_NAMES' in channels:
                return channels['CHANNEL_NAMES']
            return []
    except FileNotFoundError:
        print(f"Error: The file '{yaml_path}' was not found.")
        return []
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file '{yaml_path}': {e}")
        return []

def write_channel_id(channel_name, channel_id, yaml_path='yamls/channel_ids.yaml'):
    """
    Writes a channel name and its ID to a YAML file, handling duplicate names.

    Args:
        channel_name (str): The name of the YouTube channel.
        channel_id (str): The ID of the YouTube channel.
        yaml_path (str): The path to the YAML file to write to.
    """
    data = {}
    try:
        with open(yaml_path, 'r') as file:
            data = yaml.safe_load(file)
            if data is None:
                data = {}
    except FileNotFoundError:
        print(f"Creating new file: '{yaml_path}'")
        pass # File will be created

    if 'CHANNEL_IDS' not in data:
        data['CHANNEL_IDS'] = {}

    # Check if the channel_id already exists for ANY channel name
    existing_id = None
    existing_name = None
    for name, cid in data['CHANNEL_IDS'].items():
        if cid == channel_id:
            existing_id = cid
            existing_name = name
            break

    if existing_id:
        if existing_name == channel_name:
            print(f"Channel '{channel_name}' with ID '{channel_id}' already exists. Skipping write.")
            return
        else:
            print(f"Channel ID '{channel_id}' already exists for channel name '{existing_name}'. Appending counter to new name '{channel_name}'.")
            # Fall through to creating a duplicate entry with a modified name
    
    # Handle duplicate *names* if the ID is new or if we are creating a duplicate entry for the same ID
    original_channel_name = channel_name
    counter = 1
    while channel_name in data['CHANNEL_IDS']:
        channel_name = f"{original_channel_name} ({counter})"
        counter += 1

    data['CHANNEL_IDS'][channel_name] = channel_id

    try:
        with open(yaml_path, 'w') as file:
            yaml.safe_dump(data, file, indent=4)
        print(f"Successfully added/updated channel '{channel_name}' with ID '{channel_id}' in '{yaml_path}'.")
    except yaml.YAMLError as e:
        print(f"Error writing to YAML file '{yaml_path}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred while writing to '{yaml_path}': {e}")

if __name__ == "__main__":
    print("Starting YouTube Channel Processor...")
    channel_names = read_channel_names()

    if not channel_names:
        print("No channel names found or an error occurred. Exiting.")
    else:
        print(f"Found {len(channel_names)} channels to process: {channel_names}")
        for name in channel_names:
            print(f"Processing channel: {name}")
            channel_id = get_channel_id_from_youtube(name)
            if channel_id:
                write_channel_id(name, channel_id)
            else:
                print(f"Could not retrieve channel ID for '{name}'. Skipping.")
    print("YouTube Channel Processor finished.")