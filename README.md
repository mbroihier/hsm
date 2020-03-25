# hsm - Hotspot Monitor

This repository contains code for implementing a hotspot monitor on a Raspberry PI.  The code implements a hotspot/access point on a PI tethered to a phone.  A display server is started so that an observer can monitor, in real time, the amount of traffic going through the hotspot and can look at which links are utilizing the most traffic.  I've installed this on Stretch and Buster versions of Raspbian.  When installing this, I recommend that you use the PI that you intend to use as the hotspot.  Using this approach avoids driver installation issues that make hostapd inoperable.  Since my initial release, I've added instructions for installing Pi-hole.  I did this to reduce traffic when using my mobile data.  I also did this to have access to URLs from the Pi-hole database.  I use this information to map IP addresses to URLs to help clarify what applications are using large amounts of data. 

The latest release of HSM to GITHUB has changes to real time monitoring to fix a hang when logs rotate.  Additionally, several design and name changes were made to clarify purpose, functionality, and reduce stress on browsers when they pull up utilization graphs.  With better response time and more information displayed on data point hovers, users should find the display more useful in tracking down data hogs.

![Alt text](/main.png?raw=true "Main page of file server")
![Alt text](/detail.png?raw=true "Detailed Graph of a Log")


Installation

  1)  Install Buster Lite from www.raspberrypi.org/downloads/raspbian
      I do headless installs of my PI's which, on this publication date
      means that I copy the raspbian image to the SD card plugged into my
      Mac, mount the card and touch the ssh file on the boot partition.
      
      Note that initially you will want to be on your home's network 
      with an ethernet cable so that you can update your image and
      install necessary packages from the Internet and won't be affected
      by the adjustments made to the wlan0 interface.
  2)  Put the SD card in your target PI and boot it.
  3)  Change the password.
  4)  Change the node name to hsm.
  5)  sudo apt-get update
  6)  sudo apt-get upgrade
  7)  sudo apt-get install git
  8)  sudo apt-get install hostapd
      - if this fails (seems to on PI 4's), do this:
        + sudo systemctl unmask hostapd
        + sudo systemctl enable hostapd
  9)  sudo apt-get install dnsmasq
 10)  sudo apt-get install nodejs
 11)  sudo apt-get install npm
 12)  git clone https://github.com/mbroihier/hsm
 13)  cd hsm
 14)  sudo cp -p hsm.service /lib/systemd/system/ 
 15)  sudo systemctl enable hsm.service
 16)  To install the access point setup, type ./apinstall on the command line (this script was inspired by Cornelius Keck)
      - ./apinstall 
 17)  change the SSID and password in the hostapd.conf file
 18)  Install the node.js libraries 
      - npm install
 19)  Enable IP forwarding by editing /etc/sysctl.conf
 20)  Reboot, once booted, the hotspot and hotspot monitor should be active.  If you do not want Pi-hole, stop here.
      - sudo shutdown -r now
 21)  Using a device attached to the hotspot network (it should be available after boot), log into the hotspot (192.168.100.1).
 22)  Tether your phone to the Raspberry PI using an USB interface cable with appropriate adapters.  At this point, to reduce consumption of your mobile data, you want your phone connected to your home wifi.  
 23)  Stop dnsmasq.  This is being done so that during the install of Pi-hole, the disabling of dnsmasq does not terminate DNS functionality.
      - sudo systemctl stop dnsmasq
 24)  Check to see if you have access to a name server
      - ping www.google.com
 25)  If you can't ping www.google.com, then edit /etc/resolv.conf and replace 127.0.0.1 with 8.8.8.8 as the name server IP address
      - sudo vi /etc/resolv.conf
 26)  Ping again to make sure you can now ping google.
 27)  cd hsm
 28)  git clone --depth 1 https://github.com/pi-hole/pi-hole.git Pi-hole
 29)  cd "Pi-hole/automated install/"
 30)  sudo bash basic-install.sh
 31)  When questioned, select the wlan0 lan, and set your host address and gateway to 192.168.100.1 (from your /etc/network/interfaces file).
 32)  When complete, change your Pi-hole password to something you can remember
      - pihole -a -p
 33)  Connect a device with a browser to your network and bring up the browser and navigate to the Pi-hole admin console (http://192.168.100.1/admin) and log into the administrator account.
 34)  Click on Setup and setup the DHCP server (enable it and save it - maybe adjust your range depending on the number of clients you want to support).
 35)  After logging out of the Pi-hole admin account, reboot the raspberry pi from your login console.  After the PI comes up, devices connecting to your hotspot will automatically have their requests to known ad servers filtered out by Pi-hole.

This procedure has been used with PI 0's, PI 3's, and PI 4's.  On the PI 3's, I've installed Stretch "lite" Raspbian.  On PI 0's and PI 4's I've installed Buster "lite" Raspbian.

**** Note ****
When hsm is first installed, annotation (translation of IPs to URLs) is effectively disabled.  This is because Pi-hole has not built up its database and the build_url_ip_db script has not been run.  Depending on how many URLs have been collected by Pi-hole, build_url_ip_db can take some time to run (for 5000-6000 URLs I've seen it take ~ 100 seconds on a PI 0).  build_url_ip_db must be run to annotate IP addresses on graphs. On the "Process New Logs" web page, if you check the update annotation check box prior to pressing the yes button, the annotation database will be refreshed/built.

