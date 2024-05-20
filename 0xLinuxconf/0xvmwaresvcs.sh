sudo systemctl enable vmware-networks.service  vmware-usbarbitrator.service 
sudo systemctl start vmware-networks.service  vmware-usbarbitrator.service 
sudo modprobe -a vmw_vmci vmmon
