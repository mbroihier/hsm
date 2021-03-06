#!/usr/bin/env python3
'''
Process the logs produced by iptables
'''
import getopt
import json
import re
import sys
import time

class MonitoredLogToJS():
    '''
    Class that handles the parsing of the monitor log into Javascript plot snippets
    '''
    def __init__(self, log_file, plot_info_file_path):
        '''
        Constructor
        '''
        self.file_handle = open(log_file, "r")
        self.plot_info_file_path = plot_info_file_path
        self.boot = 1
        self.series = {}
        self.compacted_series = {}
        self.series["all"] = []
        self.is_forward =  re.compile(r" \[\s*(\d+\.\d+)\]\sFWD:.+?\sSRC=([0-9\.]+)\sDST=([0-9\.]+)\sLEN=(\d+)\s")
        self.local_network = re.compile(r"192.168")

    def compact_collected_link_information(self):
        '''
        Compact the series information so that it can display in reasonable time
        '''
        link_threshold = {}
        for link in self.series:
            if not '<-->' in link:
                link_threshold[link] = int(0.0025 * self.series[link][-1][1])

        for link in self.series:
            points = len(self.series[link])
            link_bytes = self.series[link][-1][1]
            if link in link_threshold:
                threshold = link_threshold[link]
            else:
                local_lan_host = link.split("<-->")[0]
                if local_lan_host in link_threshold:
                    threshold = link_threshold[local_lan_host]
                else:
                    # this should not happen
                    threshold = 0
                    print(local_lan_host, link)

            points_in_compacted_range = 1000
            if link_bytes > threshold:
                delta = (points - 1) / points_in_compacted_range
                if delta <= 1.0:
                    delta = 1.0
                self.compacted_series[link] = []
                points = min(points, points_in_compacted_range)
                for offset in range(points):
                    try:
                        index = int(offset * delta)
                        self.compacted_series[link].append(self.series[link][index])
                    except IndexError:
                        print(index)

                self.compacted_series[link].append(self.series[link][-1])

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
                    self.series[destination].append(
                        [time_stamp, self.series[destination][-1][1] + packet_length])
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
        all_bytes = 0
        next_time_stamp = 0
        last_time_stamp = 0

        start = time.time()
        while line != "":
            match = self.is_forward.search(line)
            if match: # this is a trace with data being forwarded
                time_stamp, source, destination, packet_length = match.group(1, 2, 3, 4)
                packet_length = int(packet_length)
                time_stamp = float(time_stamp)
                all_bytes += packet_length
                if time_stamp < last_time_stamp:
                    # a boot has been detected, write previously collected information
                    # and then continue with next boot section
                    self.write()
                    all_bytes = 0
                    next_time_stamp = 0
                last_time_stamp = time_stamp
                if time_stamp >= next_time_stamp:
                    self.series["all"].append([time_stamp, all_bytes])
                    next_time_stamp = time_stamp + 30.0
                self.store_by_source_and_destination(source, destination, time_stamp, packet_length)
            else:
                print("Rejecting", line.rstrip())
            line = self.file_handle.readline().strip()
        self.series["all"].append([time_stamp, all_bytes])
        print("parsing time:", time.time() - start)

    def write(self):
        '''
        Write JavaScript file for one "boot" section of the log
        '''
        self.compact_collected_link_information()
        javascript_string = "var collectedData = JSON.parse('"
        javascript_string += json.dumps(self.compacted_series)
        javascript_string += "');"
        output_file = open(self.plot_info_file_path + "_" + str(self.boot) + ".js", "w")
        output_file.write(javascript_string)
        output_file.close()
        self.boot += 1
        self.series = {}
        self.compacted_series = {}
        self.series["all"] = []

def main():
    '''
    main program
    '''
    source = ""
    destination = ""
    help_string = "process_iptable_logs.py <file to convert> <plot_file_prefix>"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", [])
        for opt, arg in opts:
            if  opt:
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
    log_to_json = MonitoredLogToJS(source, destination)
    log_to_json.parse_log()
    log_to_json.write()

if __name__ == '__main__':
    main()
