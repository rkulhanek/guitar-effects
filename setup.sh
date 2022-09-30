#!/bin/bash

DIR=$(dirname $(realpath $0))
cd "$DIR"

# TODO: add all the apt install stuff here, compile start.d, etc.

# Symlinks
ln -s $(realpath jackdrc) ~/.jackdrc
mkdir -p ~/.config/autostart
ln -s $(realpath guitarix-config) ~/.config/guitarix

# Destktop entry
AUTOSTART="$HOME/.config/autostart/start.desktop"
cat > "$AUTOSTART" <<-EOF
	[Desktop Entry]
	Encoding=UTF-8
	Name=Start
	Type=Application
	Exec=$DIR/start.sh
EOF
chmod u+x "$AUTOSTART"

# Utilities
pip install rtcqs

