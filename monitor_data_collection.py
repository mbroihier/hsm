#!/usr/bin/env python3
'''
Monitor Data Collection
'''
import getopt
import json
import os
import re
import sys
import time

class MonitorLogToJS(object):
    '''
    Class that handles the parsing of the monitor log into Javascript plot snippets
    '''
    def __init__(self, log_file, plot_info_file):
        '''
        Constructor
        '''
        self.file_handle = open(log_file, "r")
        self.plot_info_file = plot_info_file.replace(".js","")
        self.boot = 1
        self.output_file = open(self.plot_info_file + "_" + str(self.boot) + ".js", "w")
        self.series = {}
        self.series["all"] = []
        self.is_forward = re.compile(r" FWD")
        self.is_inbound = re.compile(r"IN=wlan")
        self.is_outbound = re.compile(r"IN=usb")
        self.packet_length = re.compile(r"LEN=(\d+)")
        self.source = re.compile(r"SRC=([0-9\.]+)")
        self.destination = re.compile(r"DST=([0-9\.]+)")
        self.local_network = re.compile(r"192.168.100")
        self.time_stamp = re.compile(r" \[ *(\d+\.\d+)\]")

    def store_by_source_and_destination(self, source, destination, time_stamp, packet_length):
        '''
        Store totals by source and destination
        '''
        path = ""
        if self.local_network.search(source):
            path = source + "<-->" + destination
            if source in self.series:
                self.series[source].append([time_stamp, self.series[source][-1][1] + packet_length])
            else:
                self.series[source] = []
                self.series[source].append([time_stamp, packet_length])

        else:
            if self.local_network.search(destination):
                path = destination + "<-->" + source
                if destination in self.series:
                    self.series[destination].append([time_stamp, self.series[destination][-1][1] + packet_length])
                else:
                    self.series[destination] = []
                    self.series[destination].append([time_stamp, packet_length])
            else:
                path = "unexpected"

        if path in self.series:
            self.series[path].append([time_stamp, self.series[path][-1][1] + packet_length])
        else:
            self.series[path] = []
            self.series[path].append([time_stamp, packet_length])
        
    def parse_log(self):
        '''
        Parse the log file into JSON
        '''
        line = self.file_handle.readline().strip()
        incoming_total = 0
        outgoing_total = 0
        all_bytes = 0
        next_time_stamp = 0
        offset = 0
        last_time_stamp = 0
        
        while line != "":
            if self.is_forward.search(line): # this is a trace with data being forwarded
                match = self.packet_length.search(line)
                packet_length = int(match.group(1))
                all_bytes += packet_length
                match = self.source.search(line)
                source = match.group(1)
                match = self.destination.search(line)
                destination = match.group(1)
                match = self.time_stamp.search(line)
                time_stamp = float(match.group(1))
                if time_stamp < last_time_stamp:
                    #offset += last_time_stamp + 1000
                    #print("bumping offset: " + str(offset))
                    self._write()
                    all_bytes = 0
                    next_time_stamp = 0
                    offset = 0
                    last_time_stamp = 0
                    
                last_time_stamp = time_stamp
                time_stamp += offset
                if time_stamp >= next_time_stamp:
                    self.series["all"].append([time_stamp, all_bytes])
                    next_time_stamp = time_stamp + 1.0
                self.store_by_source_and_destination(source, destination, time_stamp, packet_length)
            line = self.file_handle.readline().strip()

    def write(self):
        '''
        Write JavaScript file
        '''
        javascript_string = "var collectedData = JSON.parse('"
        javascript_string += json.dumps(self.series)
        javascript_string += "');"
        self.output_file.write(javascript_string)
        self.output_file.close()

    def _write(self):
        '''
        Write intermediate JavaScript file
        '''
        javascript_string = "var collectedData = JSON.parse('"
        javascript_string += json.dumps(self.series)
        javascript_string += "');"
        self.output_file.write(javascript_string)
        self.output_file.close()
        self.boot += 1
        self.output_file = open(self.plot_info_file + "_" + str(self.boot) + ".js", "w")
        self.series = {}
        self.series["all"] = []

def main():
    '''
    main program
    '''
    source = ""
    destination = ""
    file_type = "json"
    help_string = "monitor_data_collection.py <file to convert> <plot_file_prefix>"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["js"])
        for opt, arg in opts:
            if  opt == "--js":
                file_type = "javascript"
            else:
                print(help_string)
                sys.exit(-1)
        for arg in args:
            if source == "":
                source = arg
            else:
                if destination == "":
                    destination = arg
                else:
                    print(help_string)
                    sys.exit(-1)
    except getopt.GetoptError:
        print(help_string)
        sys.exit(-1)
    log_to_json = MonitorLogToJS(source, destination)
    log_to_json.parse_log()
    log_to_json.write()

if __name__ == '__main__':
    main()

