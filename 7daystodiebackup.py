import os
import shutil
from datetime import datetime, timedelta
import time
from pathlib import Path

# Change the working directory to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Get the current user's home directory dynamically
home_dir = str(Path.home())
backup_folder = os.path.join(home_dir, "AppData", "Roaming", "7DaysToDie", "Backups")

# Default settings
default_backup_frequency = 60  # in minutes
default_max_saves = 24
default_delete_old_saves = 'no'

def prompt_with_default(prompt_text, default_value):
    user_input = input(f"{prompt_text} [{default_value}]: ")  # Display the default value in brackets
    return user_input.strip() or default_value  # Use the default if input is empty



# Prompt for backup frequency, max saves, and delete old saves
backup_frequency = int(prompt_with_default("Enter backup frequency in minutes", 60))
max_saves = int(prompt_with_default("Enter max saves to keep", 24))
delete_old_saves = prompt_with_default("Delete old saves (yes/no)", "no").lower() == "yes"
backup_folder = prompt_with_default("Enter backup folder", os.path.join(home_dir, "AppData", "Roaming", "7DaysToDie", "Backups"))

# Print to verify values
print(f"Backup Frequency: {backup_frequency} minutes")
print(f"Max Saves: {max_saves}")
print(f"Backup Folder: {backup_folder}")
print(f"Delete Old Saves: {delete_old_saves}")

# Set source directory
source_dir = os.path.join(home_dir, "AppData", "Roaming", "7DaysToDie", "Saves")

# Ensure the backup directory exists
if not os.path.exists(backup_folder):
    os.makedirs(backup_folder)
    print(f"Backup folder created: {backup_folder}")

# Function to get current time in HH:MM:SS format
def current_time():
    return datetime.now().strftime('%H:%M:%S')

# Function to print messages with a timestamp
def print_with_timestamp(message):
    print(f"[{current_time()}] {message}")

# Function to search for folders containing players.xml
def find_players_xml_folders(root_dir):
    folders_with_players = []
    for root, dirs, files in os.walk(root_dir):
        if 'players.xml' in files:
            relative_folder = os.path.relpath(root, root_dir)
            folder_name = os.path.basename(os.path.normpath(root))
            parent_folder = os.path.basename(os.path.dirname(root))
            folders_with_players.append((relative_folder, f"{parent_folder} - {folder_name}"))
    return folders_with_players

# Function to copy the selected folder with a new structure
def copy_folder_with_structure(src_folder, parent_folder, dest_folder):
    # Generate the new folder name with the current date and time
    folder_name = os.path.basename(src_folder)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    new_folder_name = f"{timestamp} {folder_name}"
    
    # Create the new folder path in the destination directory
    full_dest_path = os.path.join(dest_folder, new_folder_name)
    
    # If the destination folder already exists, remove it
    if os.path.exists(full_dest_path):
        print_with_timestamp(f"Destination folder already exists. Overwriting: {full_dest_path}")
        shutil.rmtree(full_dest_path)  # Delete the existing folder

    # Create the new folder in the destination directory
    os.makedirs(full_dest_path, exist_ok=True)

    # Copy the entire parent folder (e.g., Pregen04k4) into the new timestamped folder
    parent_folder_path = os.path.join(source_dir, parent_folder)
    shutil.copytree(parent_folder_path, os.path.join(full_dest_path, os.path.basename(parent_folder)))

    print_with_timestamp(f"Folder copied and renamed to: {full_dest_path}")

# Function to validate the number of saves to keep
def get_max_saves():
    # Use value from user input
    return max_saves

# Function to prompt user and select which folder to back up
def select_folder_for_backup():
    # Find all folders containing players.xml
    folders = find_players_xml_folders(source_dir)

    # If no folders found, exit
    if not folders:
        print_with_timestamp("No folders with 'players.xml' found.")
        return None, None

    # Prompt the user to select which folder to back up
    print_with_timestamp("What file to backup?")
    for i, (relative_folder, display_name) in enumerate(folders, 1):
        print(f"{i} - {display_name}")

    # Get user input for selection
    selection = int(input("\nEnter the number of the folder to backup: ")) - 1

    # Get the selected folder
    selected_folder = folders[selection][0]
    parent_folder = selected_folder.split(os.sep)[0]  # This gets the top-level folder (e.g., Pregen04k4)
    return selected_folder, parent_folder

# Function to delete the oldest saves if the limit is exceeded
def manage_saves_limit(dest_folder, max_saves, initial_run):
    # Check if the destination folder exists
    if not os.path.exists(dest_folder):
        print_with_timestamp(f"Backup folder does not exist: {dest_folder}. Skipping save management.")
        return

    # Get a list of all backup folders in the destination directory
    backups = [f for f in os.listdir(dest_folder) if os.path.isdir(os.path.join(dest_folder, f))]
    backups.sort(key=lambda x: os.path.getctime(os.path.join(dest_folder, x)))  # Sort by creation time

    # If the number of backups exceeds the limit, delete the oldest ones
    if len(backups) > max_saves:
        excess_saves = len(backups) - max_saves
        print_with_timestamp(f"Found {len(backups)} saves, but the maximum allowed is {max_saves}.")
        
        # Delete saves if configured to do so
        if delete_old_saves:
            for i in range(excess_saves):
                oldest_backup = backups[i]
                print_with_timestamp(f"Automatically deleting {oldest_backup} since it's the oldest.")
                shutil.rmtree(os.path.join(dest_folder, oldest_backup))
        else:
            print_with_timestamp("Deletion of old saves is disabled.")

# Function to calculate and print time notifications
def print_time_notifications(backup_frequency, next_backup_time):
    now = datetime.now()
    # Calculate minutes remaining to next backup
    time_delta = next_backup_time - now
    minutes_remaining = max(0, int(time_delta.total_seconds() // 60))
    
    if minutes_remaining > 0:
        print_with_timestamp(f"Backup in {minutes_remaining} minute(s)")
    else:
        # Only show seconds countdown if less than a minute remaining
        for seconds_remaining in range(15, 0, -1):
            print_with_timestamp(f"Backup in {seconds_remaining} seconds")
            time.sleep(1)  # Wait for 1 second before the next print
        print_with_timestamp("Backup now!")

# Main function to manage the backup process
def run_backup_loop():
    # Select folder to back up
    selected_folder, parent_folder = select_folder_for_backup()

    # If no valid folder was selected, return
    if not selected_folder:
        return

    # Manage saves limit before initial backup
    initial_run = True  # Variable to track if it's the initial run
    manage_saves_limit(backup_folder, max_saves, initial_run)  # Manage saves first

    # Immediate backup before starting the first interval
    print_with_timestamp("Creating backup...")
    full_folder_path = os.path.join(source_dir, selected_folder)
    copy_folder_with_structure(full_folder_path, parent_folder, backup_folder)  # Perform initial backup

    # Set initial_run to False after the first backup
    initial_run = False

    # Calculate the time for the next backup
    next_backup_time = datetime.now() + timedelta(minutes=backup_frequency)

    # Start interval backups
    while True:
        print_with_timestamp(f"Next backup in {backup_frequency} minute(s) at {next_backup_time.strftime('%H:%M:%S')}.")

        # Wait for the next backup time
        while True:
            now = datetime.now()
            time_delta = next_backup_time - now
            total_seconds_remaining = int(time_delta.total_seconds())

            # Check if it's time to back up
            if total_seconds_remaining <= 0:
                print_with_timestamp("Creating backup...")
                manage_saves_limit(backup_folder, max_saves, initial_run)  # Check saves, but no user prompt now
                copy_folder_with_structure(full_folder_path, parent_folder, backup_folder)

                # Update the next backup time accurately after the backup
                next_backup_time = datetime.now() + timedelta(minutes=backup_frequency)
                break

            # Adjust the print interval based on the time remaining
            if total_seconds_remaining > 1200:  # More than 20 minutes remaining
                if total_seconds_remaining % 600 == 0:  # Print every 10 minutes
                    print_with_timestamp(f"Backup in {total_seconds_remaining // 60} minute(s)")
            elif total_seconds_remaining > 300:  # Between 5 and 20 minutes remaining
                if total_seconds_remaining % 300 == 0:  # Print every 5 minutes
                    print_with_timestamp(f"Backup in {total_seconds_remaining // 60} minute(s)")
            elif total_seconds_remaining > 0:  # Less than or equal to 5 minutes remaining
                if total_seconds_remaining % 60 == 0:  # Print every minute
                    print_with_timestamp(f"Backup in {total_seconds_remaining // 60} minute(s)")

            # Handle countdown in the last 10 seconds
            if total_seconds_remaining < 11:
                for seconds_remaining in range(total_seconds_remaining, 0, -1):
                    print_with_timestamp(f"Backup in {seconds_remaining} seconds")
                    time.sleep(1)  # Wait for 1 second before the next print

            # Wait for a short while before checking again
            time.sleep(1)  # Sleep for a short while before checking again

# Run the backup process
run_backup_loop()

