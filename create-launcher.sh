#!/bin/bash

# FileIndexer Desktop Launcher Creator
# This script creates a desktop launcher for FileIndexer

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Creating desktop launcher for FileIndexer...${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create an AppleScript application
LAUNCHER_PATH="$HOME/Desktop/FileIndexer.app"

# Create the app bundle structure
mkdir -p "$LAUNCHER_PATH/Contents/MacOS"
mkdir -p "$LAUNCHER_PATH/Contents/Resources"

# Create the executable script
cat > "$LAUNCHER_PATH/Contents/MacOS/FileIndexer" << 'EOF'
#!/bin/bash

# Get the directory where FileIndexer is installed
INSTALL_DIR="INSERT_INSTALL_DIR"

# Open Terminal and run the start script
osascript <<END
tell application "Terminal"
    activate
    do script "cd '$INSTALL_DIR' && ./start-fileindexer.sh"
end tell
END

# Wait a bit then open the browser
sleep 5
open "http://localhost:3000"
EOF

# Replace the placeholder with actual install directory
sed -i '' "s|INSERT_INSTALL_DIR|$SCRIPT_DIR|g" "$LAUNCHER_PATH/Contents/MacOS/FileIndexer"

# Make it executable
chmod +x "$LAUNCHER_PATH/Contents/MacOS/FileIndexer"

# Create Info.plist
cat > "$LAUNCHER_PATH/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>FileIndexer</string>
    <key>CFBundleName</key>
    <string>FileIndexer</string>
    <key>CFBundleIdentifier</key>
    <string>com.fileindexer.app</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
EOF

echo -e "${GREEN}Desktop launcher created!${NC}"
echo -e "${YELLOW}Location: $LAUNCHER_PATH${NC}"
echo ""
echo -e "${BLUE}You can now:${NC}"
echo -e "1. Double-click ${YELLOW}FileIndexer.app${NC} on your Desktop"
echo -e "2. Or drag it to your Applications folder"
echo -e "3. Or add it to your Dock for quick access"
echo ""
echo -e "${YELLOW}Note: The first time you run it, macOS may ask for permission.${NC}"
echo -e "${YELLOW}Click 'Open' to allow it to run.${NC}"
echo ""
