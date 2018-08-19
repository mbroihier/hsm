#!/usr/bin/env python3
'''
Flow meter
'''
import getopt
import json
import os
import re
import pipes
import sys
import time

class Local_Pipe(object):
    '''
    Class that handles the pipe formation of the flow
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.in_template = pipes.Template()
        self.in_template.debug(True)
        self.in_template.prepend("tail -f /var/log/kern.log", ".-")
        self.in_template.append("grep FWD", "--")
        self.in_flow_pipe = self.in_template.open('flowpipe',"r")
        self.packet_length = re.compile(r"LEN=(\d+)")
        self.time_stamp = re.compile(r" \[ *(\d+\.\d+)\]")


    def write_to_pipe(self):
        '''
        Get stuff from the kernel log and write it to the stdout pipe
        '''
        line = self.in_flow_pipe.readline()
        last_time_stamp = 0
        offset=0
        next_time_stamp = 0
        all_bytes = 0
        while line != "":
            match = self.packet_length.search(line)
            packet_length = int(match.group(1))
            all_bytes += packet_length
            match = self.time_stamp.search(line)
            time_stamp = float(match.group(1))
            if time_stamp < last_time_stamp:
                offset += last_time_stamp + 1000
                print("bumping offset: " + str(offset))
            last_time_stamp = time_stamp
            time_stamp += offset
            if time_stamp >= next_time_stamp:
                print(str(time_stamp) + ", " + str(all_bytes))
                sys.stdout.flush()
                next_time_stamp = time_stamp + 1.0
            line = self.in_flow_pipe.readline()
        print("leaving write to pipe")
        
def main():
    '''
    main program
    '''
    source = ""
    destination = ""
    help_string = "flow_meter.py"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "")
        for opt in opts:
            if  opt is not None:
                print('options detected: ' + opt)
                print(help_string)
                sys.exit(-1)
        for arg in args:
            if arg is not None:
                print('args detected')
                print(help_string)
                sys.exit(-1)
    except getopt.GetoptError:
        print('Exception')
        print(help_string)
        sys.exit(-1)
    pipe = Local_Pipe()
    pipe.write_to_pipe()

if __name__ == '__main__':
    main()

