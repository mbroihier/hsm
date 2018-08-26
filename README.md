# hsm - Hotspot Monitor

This repository contains code for implementing a hotspot monitor on a Raspberry PI.  The code implements a hotspot/access point on a PI tethered to a phone.  A display server is started so that an observer can monitor, in real time, the amount of traffic going through the hotspot and can look at which links are utilizing the most traffic.

![Alt text](/main.png?raw=true "Main page of file server")
![Alt text](/detail.png?raw=true "Detailed Graph of a Log")


Installation

  1)  Install Stretch Lite from www.raspberrypi.org/downloads/raspbian
      I do headless installs of my PI's which, on the publication date
      means that I copy the raspbian image to the SD card plugged into my
      Mac, mount the card and touch the ssh file on the boot partition.
      
      Note that initially you will want to be on your home's network 
      with an ethernet cable so that you can update your image and
      install necessary packages from the Internet and won't be affected
      by the adustments made to the wlan0 interface.
  2)  Boot the pi off the installed image.
  3)  Change the password.
  4)  Change the node name to hsm.
  5)  sudo apt-get update
  6)  sudo apt-get install git
  7   sudo apt-get install hostapd
  8)  sudo apt-get install dnsmasq
  9)  sudo apt-get install nodejs
 10)  sudo apt-get install npm
 11)  git clone https://github.com/mbroihier/hsm
 12)  cd hsm
 13)  sudo cp -p hsm.service /lib/systemd/system/ 
 14)  sudo systemctl enable hsm.service
 15)  To install the access point setup, type ./apinstall on the command line (this script was inspired by Cornelius Keck) 
 16)  change the SSID and password in the hostapd.conf file
 17)  Install the node.js libraries by typing npm install
 18)  reboot with sudo shutdown -r now

When the PI comes up, you should be able to login to it from your access point network at address 192.168.100.1.  You should find a file server running at http://192.168.100.1:3000.  If you connect a USB cable to your smart phone and enable USB tethering, you should have access to the web through the hotspot.




