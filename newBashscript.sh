#!/bin/bash

# Ask for the user's name using a dialog box
NAME=$(zenity --entry --title="Name Input" --text="Please enter your name:")

# Check if the user pressed Cancel or closed the dialog
if [ $? -eq 0 ]; then
    echo "Your name is: $NAME"
else
    echo "No name entered."
fi