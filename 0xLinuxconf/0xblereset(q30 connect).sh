#!/bin/bash
sudo systemctl restart bluetooth.service
sleep 3
sudo bluetoothctl connect 98:47:44:A3:2D:D0
sudo bluetoothctl trust
