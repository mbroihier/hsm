#!/usr/bin/env python3
'''
Monitor Data Collection
'''
import json
import os
import re
import sys
import time

class MonitorLogToJson(object):
    '''
    Class that handles the parsing of the monitor log into JSON
    '''
    def __init__(self, log_file, json_file):
        '''
        Constructor
        '''
        self.file_handle = open(log_file, "r")
        self.output_file = open(json_file, "w")
        self.series = {}
        self.series["inbound traffic"] = []
        self.series["inbound traffic total"] = []
        self.series["outbound traffic"] = []
        self.series["outbound traffic total"] = []
        self.is_forward = re.compile(r" FWD")
        self.is_inbound = re.compile(r"IN=wlan")
        self.is_outbound = re.compile(r"IN=usb")
        self.packet_length = re.compile(r"LEN=(\d+)")
        self.source = re.compile(r"SRC=([0-9\.]+)")
        self.destination = re.compile(r"DST=([0-9\.]+)")
        self.time_stamp = re.compile(r" \[ (\d+\.\d+)\]")

    def parse_log(self):
        line = self.file_handle.readline().strip()
        incoming_total = 0
        outgoing_total = 0
        while line != "":
            if self.is_forward.search(line): # this is a trace with data being forwarded
                match = self.packet_length.search(line)
                packet_length = int(match.group(1))
                match = self.source.search(line)
                source = match.group(1)
                match = self.destination.search(line)
                destination = match.group(1)
                match = self.time_stamp.search(line)
                time_stamp = float(match.group(1))
                if self.is_inbound.search(line): #packet is coming into phone network
                    incoming_total = incoming_total + packet_length
                    self.series["inbound traffic"].append([time_stamp, packet_length])
                    self.series["inbound traffic total"].append([time_stamp, incoming_total])
                    print(match.group(1) + " " + source + " " + destination + ": " + str(packet_length) + " " + str(incoming_total))
                else:
                    outgoing_total = incoming_total + packet_length
                    self.series["outbound traffic"].append([time_stamp, packet_length])
                    self.series["outbound traffic total"].append([time_stamp, outgoing_total])
                    print(match.group(1) + " " + source + " " + destination + ": " + str(packet_length) + " " + str(outgoing_total))
            line = self.file_handle.readline().strip()
        json.dump(self.series, self.output_file)
        self.output_file.close()

def main(source, destination):
    '''
    main program
    '''

    log_to_json = MonitorLogToJson(source, destination)
    log_to_json.parse_log()

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

