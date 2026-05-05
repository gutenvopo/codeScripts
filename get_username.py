#!/usr/bin/env python3

"""
Simple script to print the current username on this computer.
"""

import getpass

def main():
    username = getpass.getuser()
    print(f"Your username is: {username}")

if __name__ == "__main__":
    main()