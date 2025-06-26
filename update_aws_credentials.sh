#!/bin/bash

# Script to add/update AWS credentials for a profile with base64 decoding support

# Function to display usage
usage() {
    echo "Usage: $0 -p <profile_name> -k <access_key_id> -s <secret_access_key> [-r <region>]"
    echo "  -p: AWS profile name (required)"
    echo "  -k: AWS access key ID (required, can be base64 encoded)"
    echo "  -s: AWS secret access key (required, can be base64 encoded)"
    echo "  -r: AWS region (optional, default: us-east-1)"
    exit 1
}

# Function to check if string is base64 encoded and decode if necessary
decode_if_base64() {
    local input="$1"
    # Check if string matches base64 pattern (contains only valid base64 chars and proper length)
    if echo "$input" | grep -qE '^[A-Za-z0-9+/]+={0,2}$' && [ $(( ${#input} % 4 )) -eq 0 ]; then
        # Try to decode and verify it's not gibberish
        decoded=$(echo "$input" | base64 -d 2>/dev/null)
        if [ $? -eq 0 ] && [ -n "$decoded" ]; then
            echo "$decoded"
            return
        fi
    fi
    # If not base64 or decoding fails, return original
    echo "$input"
}

# Default region
REGION="us-east-1"

# Parse command line arguments
while getopts "p:k:s:r:" opt; do
    case $opt in
        p) PROFILE="$OPTARG";;
        k) ACCESS_KEY="$OPTARG";;
        s) SECRET_KEY="$OPTARG";;
        r) REGION="$OPTARG";;
        ?) usage;;
    esac
done

# Check if required parameters are provided
if [ -z "$PROFILE" ] || [ -z "$ACCESS_KEY" ] || [ -z "$SECRET_KEY" ]; then
    echo "Error: Profile name, access key, and secret key are required"
    usage
fi

# Decode keys if they're base64 encoded
FINAL_ACCESS_KEY=$(decode_if_base64 "$ACCESS_KEY")
FINAL_SECRET_KEY=$(decode_if_base64 "$SECRET_KEY")

# Ensure AWS credentials directory exists
AWS_DIR="$HOME/.aws"
CREDENTIALS_FILE="$AWS_DIR/credentials"

if [ ! -d "$AWS_DIR" ]; then
    mkdir -p "$AWS_DIR"
    chmod 700 "$AWS_DIR"
fi

# Check if credentials file exists, create it if it doesn't
if [ ! -f "$CREDENTIALS_FILE" ]; then
    touch "$CREDENTIALS_FILE"
    chmod 600 "$CREDENTIALS_FILE"
fi

# Function to update or add profile
update_credentials() {
    # Create temporary file
    TEMP_FILE=$(mktemp)
    
    # If profile exists, update it; if not, append it
    if grep -q "^\[$PROFILE\]$" "$CREDENTIALS_FILE"; then
        # Profile exists, update it using awk
        awk -v profile="$PROFILE" \
            -v access="$FINAL_ACCESS_KEY" \
            -v secret="$FINAL_SECRET_KEY" \
            -v region="$REGION" '
            BEGIN {found=0}
            /^\[.*\]$/ {
                if (found) {print ""; found=0}
                print $0
                if ($0 == "["profile"]") found=1
                next
            }
            found && /aws_access_key_id/ {print "aws_access_key_id = "access; next}
            found && /aws_secret_access_key/ {print "aws_secret_access_key = "secret; next}
            found && /region/ {print "region = "region; next}
            {print}
            END {if (found) print ""}
        ' "$CREDENTIALS_FILE" > "$TEMP_FILE"
    else
        # Profile doesn't exist, append it
        cp "$CREDENTIALS_FILE" "$TEMP_FILE"
        echo -e "\n[$PROFILE]" >> "$TEMP_FILE"
        echo "aws_access_key_id = $FINAL_ACCESS_KEY" >> "$TEMP_FILE"
        echo "aws_secret_access_key = $FINAL_SECRET_KEY" >> "$TEMP_FILE"
        echo "region = $REGION" >> "$TEMP_FILE"
    fi

    # Replace original file with updated version
    mv "$TEMP_FILE" "$CREDENTIALS_FILE"
}

# Execute update and confirm
update_credentials
echo "AWS credentials for profile '$PROFILE' have been updated successfully"
echo "Profile details:"
echo "  Access Key ID: $FINAL_ACCESS_KEY"
echo "  Secret Access Key: [hidden]"
echo "  Region: $REGION"
# Indicate if decoding occurred
if [ "$ACCESS_KEY" != "$FINAL_ACCESS_KEY" ]; then
    echo "  Note: Access Key was base64 decoded"
fi
if [ "$SECRET_KEY" != "$FINAL_SECRET_KEY" ]; then
    echo "  Note: Secret Key was base64 decoded"
fi
