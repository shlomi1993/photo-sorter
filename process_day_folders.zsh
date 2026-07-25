#!/bin/zsh

# Script to process "Day XXX" folders with photo-sorting
# Day 001 corresponds to 2017.09.13, and each subsequent day increments by 1

set -e  # Exit on any error

# Check if target directory is provided
if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <target_directory>"
    echo "Example: $0 '/Users/shlomibenshushan/Library/CloudStorage/OneDrive-Personal/Photos/2017/2017.09.11 - הטיול הגדול/אוסטרליה'"
    exit 1
fi

TARGET_DIR="$1"

# Check if target directory exists
if [[ ! -d "$TARGET_DIR" ]]; then
    echo "Error: Directory does not exist: $TARGET_DIR"
    exit 1
fi

# Base date for Day 001 (September 13, 2017)
BASE_DATE="2017-09-13"

echo "Processing Day folders in: $TARGET_DIR"
echo "Base date (Day 001): $BASE_DATE"
echo

# Find all Day folders (excluding Day 000) - use null delimiter to handle spaces
DAY_FOLDERS=()
while IFS= read -r -d '' folder; do
    if [[ ! "$folder" =~ "Day 000" ]]; then
        DAY_FOLDERS+=("$folder")
    fi
done < <(find "$TARGET_DIR" -maxdepth 1 -type d -name "Day [0-9][0-9][0-9]*" -print0 | sort -z)

if [[ ${#DAY_FOLDERS[@]} -eq 0 ]]; then
    echo "No Day folders found in the target directory."
    exit 0
fi

echo "Found ${#DAY_FOLDERS[@]} Day folders to process:"
for folder in "${DAY_FOLDERS[@]}"; do
    echo "  $(basename "$folder")"
done
echo

# Process each Day folder
for DAY_FOLDER in "${DAY_FOLDERS[@]}"; do
    FOLDER_NAME=$(basename "$DAY_FOLDER")
    
    # Extract day number from folder name (e.g., "Day 016 - Title" -> "016")
    if [[ "$FOLDER_NAME" =~ ^Day\ ([0-9]{3}) ]]; then
        DAY_NUM="${match[1]}"
        
        # Convert day number to integer and calculate days to add
        DAY_INT=$((10#$DAY_NUM))  # Force base 10 to handle leading zeros
        DAYS_TO_ADD=$((DAY_INT - 1))  # Day 001 = 0 days to add, Day 002 = 1 day, etc.
        
        # Calculate the target date using date command
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS date command
            TARGET_DATE=$(date -j -v+${DAYS_TO_ADD}d -f "%Y-%m-%d" "$BASE_DATE" "+%Y.%m.%d")
        else
            # Linux date command
            TARGET_DATE=$(date -d "$BASE_DATE + $DAYS_TO_ADD days" "+%Y.%m.%d")
        fi
        
        echo "Processing: $FOLDER_NAME"
        echo "  Day number: $DAY_NUM"
        echo "  Target date: $TARGET_DATE"
        echo "  Command: photo-sorting '$DAY_FOLDER' -d $TARGET_DATE"
        
        # Run the photo-sorting command
        if photo-sorting "$DAY_FOLDER" -d "$TARGET_DATE"; then
            echo "  ✓ Successfully processed $FOLDER_NAME"
        else
            echo "  ✗ Failed to process $FOLDER_NAME"
            echo "  Continuing with next folder..."
        fi
        
        echo
    else
        echo "Warning: Could not extract day number from folder name: $FOLDER_NAME"
        echo
    fi
done

echo "Processing complete!"