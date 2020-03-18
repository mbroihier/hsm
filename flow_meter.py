#!/usr/bin/env python3
'''
Flow meter
'''
import getopt
import os
import re
import select
import stat
import sys
import time

class PseudoPipe():
    '''
    Class that handles the reading of a file like a pipe
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.log_file = "/var/log/kern.log"
        self.in_flow_pipe = open(self.log_file, "r")
        self.get_info = self.forward_packet = re.compile(r"\s\[ *(\d+\.\d+)\]\sFWD:.+?\sLEN=(\d+)")
        self.inode = os.stat(self.log_file)[stat.ST_INO]

    def get_a_filtered_line(self, first_time=False):
        '''
        Get a forwarding line from the kernel log and swap log files if necessary
        '''
        got_a_line = False
        if first_time:
            self.in_flow_pipe.seek(0, 2)
        while not got_a_line:
            which = select.select([self.in_flow_pipe], [], [], 5.0)
            if self.in_flow_pipe in which[0]:
                #print("select says something to read")
                line = self.in_flow_pipe.readline()
                if line == '':  # end of file has been reached, but more may come
                    time.sleep(5.0)
                    check_for_swap = True
                else:
                    check_for_swap = False
                #print(line.rstrip())
                match = self.forward_packet.search(line)
                if match:
                    got_a_line = True
            else:
                #print("select result:", which)
                # check if pipe is stale
                check_for_swap = True
            if check_for_swap:
                check_for_swap = False
                file_error = True # not true yet, but stat may fail on log rotate
                while file_error:
                    try:
                        new_inode = os.stat(self.log_file)[stat.ST_INO]
                        if self.inode != new_inode: # log file has been rotated, swap to new one
                            self.in_flow_pipe.close()
                            self.in_flow_pipe = open(self.log_file, "r")
                            self.inode = new_inode
                        file_error = False # file error did not occur - no stat issue
                    except FileNotFoundError:
                        pass # continue in while loop
        return line
    def write_to_pipe(self):
        '''
        Get stuff from the kernel log and write it to the stdout pipe
        '''
        line = self.get_a_filtered_line(True)
        last_time_stamp = 0
        offset = 0
        next_time_stamp = 0
        all_bytes = 0
        while line != "":
            match = self.get_info.search(line)
            packet_length = int(match.group(2))
            all_bytes += packet_length
            time_stamp = float(match.group(1))
            if time_stamp < last_time_stamp:
                offset += last_time_stamp + 1000
            last_time_stamp = time_stamp
            time_stamp += offset
            if time_stamp >= next_time_stamp:
                print(str(time_stamp) + ", " + str(all_bytes))
                sys.stdout.flush()
                next_time_stamp = time_stamp + 1.0
            line = self.get_a_filtered_line()
        print("leaving write to pipe - this line should never be displayed")
def main():
    '''
    main program
    '''
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
    pipe = PseudoPipe()
    try:
        pipe.write_to_pipe()
    except KeyboardInterrupt:
        print("\nControlled exit")
        sys.exit(0)

if __name__ == '__main__':
    main()
