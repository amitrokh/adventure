#!/bin/sh
#
# Automatically try to connect to 'adventure-wifi' when WiFi is enabled
#

# the output of nmcli should be in English
LC_ALL=C

# loop for a while until NetworkManager is accepting commands
# Connection name: adventure-wifi
# SSID: <name>-wifi
# manual IP: 10.42.0.1

nmcli con up id 'adventure-wifi'
while [ "$(nmcli -t -f WIFI,STATE nm)" = 'enabled:disconnected' ]
do
 nmcli con up id 'adventure-wifi'
 sleep 5
done

exit 0
