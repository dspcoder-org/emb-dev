#!/bin/bash

# Function to display usage information
usage() {
    echo "Usage: $0 [-c] <username> <folder_name>"
    echo "       $0 [-r] <full_path_to_file> [full_path_to_file2 ...]"
    echo "  -c: Copy mode - Copy folder to user's directory"
    echo "  -r: Recovery mode - Recover specified files using their full paths"
    exit 1
}

# Check if correct number of arguments is provided
if [ $# -lt 2 ]; then
    usage
fi

# Parse mode
mode="$1"
shift

case "$mode" in
    -c)
        # Original copy mode logic
        username="$1"
        folder_name="$2"
        source_dir="/dspcoder/codeFromServer/$folder_name"
        dest_dir="/home/$username"

        # Check if source directory exists
        if [ ! -d "$source_dir" ]; then
            echo "Error: Source directory does not exist."
            exit 1
        fi  # Fixed the syntax error here (changed '}' to 'fi')

        # Function to copy files/folders excluding certain directories
        copy_excluding() {
            rsync -a --exclude="._mini-renode" --exclude="._tests" --exclude="a.out" \
                     --exclude="out.elf" --exclude="._dev" --exclude="ReadMe.md" "$1" "$2"
            find "$2" -type d -exec chmod 700 {} +
            find "$2" -type f -exec chmod 700 {} +
            chown -R "$username:$username" "$2"
        }

        echo "Copying folder to $dest_dir"
        copy_excluding "$source_dir" "$dest_dir"
        ;;

    -r)
        # New recovery mode logic that handles full paths
        for full_path in "$@"; do
            # Extract username and relative path from the full path
            # Assuming path format: /home/username/rest/of/path
            if [[ ! "$full_path" =~ ^/home/[^/]+/.+ ]]; then
                echo "Error: Invalid path format for $full_path"
                echo "Path should start with /home/username/"
                continue
            fi  # Added missing 'fi'

            # Extract username and folder_name from the path
            username=$(echo "$full_path" | cut -d'/' -f3)
            folder_name=$(echo "$full_path" | cut -d'/' -f4)
            rel_path=$(echo "$full_path" | cut -d'/' -f5-)

            # Set source and destination paths
            source_dir="/dspcoder/codeFromServer/$folder_name"
            source_file="$source_dir/$rel_path"
            dest_file="/home/$username/$folder_name/$rel_path"

            # Check if source file exists
            found_file=$(find "$source_dir" -path "$source_file" -not -path "*/._mini-renode/*" -not -path "*/._tests/*")
            
            if [ -n "$found_file" ]; then
                if [ -d "$found_file" ]; then
                    echo "Skipping directory: $full_path"
                    continue
                fi
                
                # Create destination directory if it doesn't exist
                dest_dir=$(dirname "$dest_file")
                mkdir -p "$dest_dir"
                
                # Copy the file
                cp "$found_file" "$dest_file"
                chmod 700 "$dest_file"
                chown "$username:$username" "$dest_file"
                echo "Recovered: $dest_file"
            else
                echo "File not found: $full_path"
            fi
        done
        ;;
    *)
        echo "Error: Invalid mode. Use -c for copy mode or -r for recovery mode."
        usage
        ;;
esac

echo "done."