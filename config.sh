 #!/bin/sh

#make ram disk
if [ ! -d "/tmp/ramdisk" ] 
then
    sudo mkdir /tmp/ramdisk
	sudo chmod 777 /tmp/ramdisk
	sudo mount -t tmpfs -o size=1024m myramdisk /tmp/ramdisk
	# nano /etc/fstab
	#myramdisk  /tmp/ramdisk  tmpfs  defaults,size=1G,x-gvfs-show  0  0
	echo "myramdisk  /tmp/ramdisk  tmpfs  defaults,size=1G,x-gvfs-show  0  0" | sudo tee -a /etc/fstab
	echo "" | sudo tee -a /etc/fstab
	sudo mount -a

fi


#auto remove no use
sudo apt-get -y remove python-pygame
sudo apt-get -y remove minecraft-pi
sudo apt -y autoremove
sudo apt-get -y purge wolfram-engine
sudo apt-get -y purge libreoffice*
sudo apt-get -y clean
sudo apt-get -y autoremove

#setting up raspi share network
sudo sysctl -w net.ipv4.ip_forward=1
sudo ifconfig eth0 169.254.115.191 netmask 255.255.0.0 up
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -I FORWARD -o eth0 -s 169.254.115.191/16 -j ACCEPT
sudo iptables -I INPUT -s 169.254.115.191/16 -j ACCEPT
