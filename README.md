# hsm - HSM setup and tools

This repository contains files and setup instruction to install a hotspot monitor on a Raspberry PI.  The purpose of this monitor is to help identify how unexplained large data transfers occur in the Google Fi network.  In May of 2018, a 1.5G transfer took place while I was tethered to my phone and I was unable to identify the devices or sites involved with the transfer.  I suspect it was an iOS update from my wife's phone or some sort of OS X update on my MacPro - but both devices were supposed to be disabled for automatic updates and background downloads and there was no trace of a large file on my MacPro created at the time of the tethering.  Google was unwilling to provide me any information without a court order.  So I decided to build a monitor to help me isolate issues of this nature.

The monitor, so far, is a PI that acts as a hotspot and tethers off of my phone running in a USB tethering mode.  Presently, I have iptables logging all forwarded traffic through the PI.  I have a python program that scans the kernel logs and builds plot data snippets that I can display on a server also running on the PI.  The display server is in a separate repository in GITHUB (hsm-display-server).



