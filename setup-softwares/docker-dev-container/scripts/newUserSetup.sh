#!/bin/bash

USERNAME="dspcoder"

# Set root password
echo "root:+_+" | chpasswd

# Create new user
useradd -m -s /bin/bash $USERNAME
echo "$USERNAME:dspcoder" | chpasswd
echo "$USERNAME ALL=(ALL) NOPASSWD: /usr/bin/sh /dspcoder/scripts/setupCodeBase.sh * " >> /etc/sudoers


# Verify dspcoder folder permissions
if [ "$(stat -c "%a %U %G" /dspcoder)" != "700 root root" ]; then
    echo "Warning: /dspcoder folder permissions are not set correctly"
    echo "Fixing permissions..."
    chmod 700 /dspcoder
    chown root:root /dspcoder
fi

rm /home/$USERNAME/.profile 
rm /home/$USERNAME/.bashrc 
rm /home/$USERNAME/.bash_logout 

# command to start code-server
tmux new-session -d -s code-server su "$USERNAME" -c "code-server --bind-addr 0.0.0.0:8080 --auth none --disable-file-downloads --disable-telemetry --disable-proxy"
tmux new-session -d -s root-code-server su root -c "code-server --bind-addr 0.0.0.0:9090 --auth none --disable-telemetry --disable-proxy"

# keep trying to copy settings.json for user
while ! cp /dspcoder/settings.json /home/$USERNAME/.local/share/code-server/User/settings.json; do 
    : 
done 

# setting permissions for the settings.json file
chown $USERNAME:$USERNAME /home/$USERNAME/.local/share/code-server/User/settings.json
chmod 644 /home/$USERNAME/.local/share/code-server/User/settings.json


tail -f /dev/null
