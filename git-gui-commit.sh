#!/bin/bash

# Stage all changes
git add .

# Prompt for commit message using a GUI dialog
commit_message=$(zenity --entry --title="Commit Message" --text="Enter your commit message:")

# Check if the user provided a commit message
if [ -z "$commit_message" ]; then
    echo "Commit message cannot be empty. Aborting."
    exit 1
fi

# Commit the changes
git commit -m "$commit_message"

# Push the changes to the main branch
git push origin main