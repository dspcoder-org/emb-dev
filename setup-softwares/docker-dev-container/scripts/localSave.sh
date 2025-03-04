#!/bin/bash

# Function to display usage information
usage() {
    echo "Usage: $0 <username> <folder_name>"
    echo "  This script copies a folder from the user's directory to the localSave directory."
    exit 1
}

# Check if correct number of arguments is provided
if [ $# -ne 4 ]; then
    usage
fi

# Parse arguments
username=$1
questionID=$2
lang=$3
folder_name=$4

# Set source and destination directories
source_dir="/home/$username/$folder_name"
dest_dir="/dspcoder/localSave/$username/$questionID/$lang"

# Check if source directory exists
if [ ! -d "$source_dir" ]; then
    echo "Error: Source directory '$source_dir' does not exist."
    exit 1
fi

# Create the destination directory if it doesn't exist
mkdir -p "$dest_dir"

# Function to copy files/folders excluding 'mini-renode' and 'tests'
copy_excluding() {
    rsync -a --exclude='._mini-emb' --exclude='._tests' "$1" "$2"
}

# Perform the copy operation
echo "Saving code base .. .. .."
copy_excluding "$source_dir/" "$dest_dir"

# Check if the copy operation was successful
if [ $? -eq 0 ]; then
    echo "Save completed."
else
    echo "Error: Save failed."
    exit 1
fi

# Calculate and display the size of the copied folder
# size=$(du -sh "$dest_dir" | cut -f1)
# echo "Size of copied folder: $size"

# Count and display the number of files copied
# file_count=$(find "$dest_dir" -type f | wc -l)
# echo "Number of files copied: $file_count"
