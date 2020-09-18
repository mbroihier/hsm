# hsm - Hotspot Monitor

This repository contains code for implementing an access point/hotspot and a network monitor on a tethered Raspberry PI.  When I travel, I connect a Raspberry PI to my Android phone with a USB cable and use the Raspberry PI as the access point for my other devices (eg laptop, iPad ...).  The monitor features allow me to visually see how much data is going through the access point and to know where the data is coming from or where it is going to.  The the information gathered by the monitor can be displayed as graphs.  One display is a realtime graph that summarizes all the data going through the PI.  Other graphs are non realtime and produced on demand or when the kernel logs "rotate".

I recommend installing this on a dedicated PI and installing it from scratch.  It doesn't have to be 3 or 4 although they will work just fine.  A zero w will do the job.  I use a PI zero at home to monitor my daily traffic (excluding smart TV video).  I've installed this on Stretch and Buster versions of Raspbian, but starting with v1.5-1 I've implemented an installer that is intended to work with buster. I also recommend installing a tool such as azlux's log2ram to reduce wear on your SD card.  This should be done after the raspbian install and before the hsm install.  I also recommend installing Pi-hole because it reduces traffic (and those pesky ads) to your mobile devices.  If Pi-hole is installed, the monitor software can use its database to annotate the IP addresses to help clarify what servers are being accessed.

The monitor doesn't have to be used, the hsm service can be disabled and the hot spot/access point will still be fully functional.  If you choose to do this, you might want to contact me regarding adjustments to the iptables.  I have on my todo list, the separation of the access point installation from the monitor installation.  The access point setup by the way, was taken from files provided to me by Cornelius Keck, a former colleague of mine.  You may want to see his  LinkedIn account.


![Alt text](/main.png?raw=true "Main page of file server")
![Alt text](/detail.png?raw=true "Detailed Graph of a Log")


Installation

  1)  Install Buster Lite from www.raspberrypi.org onto an SD card following
      instructions that appeal to you.  There are quite a few variations
      discussed at numerous PI related sites.
  2)  Put the SD card in your target PI and boot it.  You will need access
      to the internet and keeping access can be tricky since the installation process
      modifies the networking.  I always do headless installs, but this is
      a time when having a keyboard and monitor directly connected to the target
      PI can save the casual user a bunch of time.
  3)  After the boot, use raspi-config to:
      - Change the password
      - Change the node name (I like hsm in this case)
      - Change the time zone (I always use UTC)
  4)  sudo reboot
  5)  sudo apt-get update
  6)  sudo apt-get upgrade
  7)  sudo reboot
  8)  Install log2ram if you are going to use it.  The instructions are at https://github.com/azlux/log2ram

Next, perform one of the following: Manual hsm Installation or hsm Package Installation.  The advantage of the Manual installation is that if trouble occurs, the ppi and complete_configuration scripts can be useful debugging aids.  Manual installation isn't all that manual, the scripts do quite a bit of magic to avoid loss of internet access and I found that using the scripts to install were more reliable than attempting to follow a lengthly step by step procedure.

Manual hsm Installation
  1)  If you choose to do a manual installation, from a bash shell on your hsm dedicated PI, do this:
      - sudo apt-get install -y git
      - git clone https://github.com/mbroihier/hsm
      - cd hsm
  2)  Execute the pseudo package installer:
      - sudo ./ppi <SSID> <password>
        + SSID is your access point name
         + password is the password you want to use

hsm Package Installation (I know, it seem longer than the manual installation ....)
  1)  Add a reference to the package by adding a file to /etc/apt/sources.list.d/:
      - sudo vi /etc/apt/sources.list.d/mbroihier.list (add the following line)
      + deb [trusted=yes] https://github.com/mbroihier/hsm/tree/master/debian/ ./
  2)  sudo apt-get update
  3)  sudo apt-get install -y hsm
  4)  Complete the setup:
      - cd /var/www/html/hsm/
      - sudo ./complete_configuraton <SSID> <password>
        + SSID is your access point name
        + password is the password you want to use

If you want Pi-hole (https://pi-hole.net), and you do, install it after you confirm your access point is functional.  Confirm functionality by attaching to your Android phone, enabling tethering, and then log onto your hotspot and confirm you have internet access by, for instance, browsing to a web site.  Bring up the monitor by browsing to http://192.168.100.1:3000.  When you install Pi-hole, you'll want it to be your DNS server which will mean that you need to disable dnsmasq (sudo systemctl stop dnsmasq and then sudo systemctl disable dnsmasq).  On my home network, Pi-hole blocks nearly 40% of the DNS requests made by typical pages I browse.  I'm a big fan.



**** Note 1 ****
When hsm is first installed, annotation (translation of IP addresses to URLs) is effectively disabled.  This is because Pi-hole has not built up its database and the build_url_ip_db script has not been run.  Depending on how many URLs have been collected by Pi-hole, build_url_ip_db can take some time to run (for 5000-6000 URLs I've seen it take ~ 100 seconds on a PI 0).  build_url_ip_db must be run to annotate IP addresses on graphs. On the "Process New Logs" web page, if you check the "update annotation" check box prior to pressing the yes button, the annotation database will be refreshed/built (but only if there is a Pi-hole database).

**** Note 2 ****
log2ram initially only has 40M of RAM disk space.  Monitor your usage and adjust as necessary.  I'm using 100M.
