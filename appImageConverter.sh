# Makes App Image an executible
file=$(zenity --file-selection --title="Select an AppImage"); [ -n "$file" ] && chmod +x "$file" && echo "✅ Made executable: $file"