#!/bin/bash

# Function to display menu
display_menu() {
    clear
    echo "AWS Profile Manager"
    echo "=================="
    echo "1. List available profiles"
    echo "2. Set active profile"
    echo "3. Exit"
    echo "=================="
}

# Function to list profiles
list_profiles() {
    echo "Available AWS Profiles:"
    echo "----------------------"
    cat ~/.aws/credentials | grep "\[" | tr -d "[]"
    echo "----------------------"
    read -p "Press Enter to continue..."
}

# Function to set active profile
set_profile() {
    list_profiles
    read -p "Enter the profile name to set as active: " profile_name
    
    if grep -q "\[$profile_name\]" ~/.aws/credentials; then
        aws configure set profile.default $profile_name
        echo "Profile '$profile_name' has been set as active."
    else
        echo "Profile '$profile_name' not found!"
    fi
    read -p "Press Enter to continue..."
}

# Main loop
while true; do
    display_menu
    read -p "Enter your choice (1-3): " choice
    
    case $choice in
        1)
            list_profiles
            ;;
        2)
            set_profile
            ;;
        3)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid option. Please try again."
            read -p "Press Enter to continue..."
            ;;
    esac
done

