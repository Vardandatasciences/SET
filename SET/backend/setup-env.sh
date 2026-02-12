#!/bin/bash
echo "Setting up environment file for Sales Intelligence Tool..."
echo

if [ -f .env ]; then
    echo ".env file already exists!"
    read -p "Do you want to overwrite it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo
echo "Please enter your Perplexity API key."
echo "You can get your API key from: https://www.perplexity.ai/settings/api"
echo
read -p "Enter your Perplexity API key: " API_KEY

if [ -z "$API_KEY" ]; then
    echo
    echo "Error: API key cannot be empty!"
    exit 1
fi

cat > .env << EOF
PERPLEXITY_API_KEY=$API_KEY
API_HOST=0.0.0.0
API_PORT=8000
EOF

echo
echo ".env file created successfully!"
echo

