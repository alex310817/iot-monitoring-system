#!/bin/bash

# First fix npm cache ownership
sudo chown -R 501:20 "/Users/ivanvergejcik/.npm"

# Clean existing installation
rm -rf node_modules
rm -f package-lock.json

# Reset npm cache
npm cache clean --force

# Install dependencies
npm install next@latest react@latest react-dom@latest --save
npm install

# Fix permissions after installation
find . -type d -exec chmod 755 {} \;
find . -type f -exec chmod 644 {} \;
[ -d "node_modules/.bin" ] && chmod +x node_modules/.bin/*
