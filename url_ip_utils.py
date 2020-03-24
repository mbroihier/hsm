#!/usr/bin/env python3
'''
Domain Name Utilities - convert domain name to IP and IP to domain name
'''
import re
import pickle
import sqlite3
import subprocess
import sys
import threading
import time

class LookupUrlIp():
    '''
    Base class of URL / IP database
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.url2ip = {}
        self.ip2url = {}
        try:
            # If directed to use the preprocessed database, load them
            file_handle = open("url2ip.db", "rb")
            self.url2ip = pickle.load(file_handle)
            file_handle.close()
            file_handle = open("ip2url.db", "rb")
            self.ip2url = pickle.load(file_handle)
            file_handle.close()
        except FileNotFoundError:
            print("Using empty database as a start")

    def dump_database(self):
        '''
        Method to dump/store (pickle) the conversion databases
        '''
        file_handle = open("url2ip.db", "wb")
        pickle.dump(self.url2ip, file_handle)
        file_handle.close()
        file_handle = open("ip2url.db", "wb")
        pickle.dump(self.ip2url, file_handle)
        file_handle.close()

    def annotate_ip(self, ip_address):
        '''
        Using an IP, annotate it if possible
        '''
        if ip_address in self.ip2url:
            ip_address = ip_address + " (" + self.ip2url[ip_address] +")"
        return ip_address

class BuildUrlIpDb(LookupUrlIp):
    '''
    Class that handles creation and update of the URL / IP database
    '''
    def __init__(self, lookup_type=None, file_path=None):
        '''
        Constructor
        '''
        super(BuildUrlIpDb, self).__init__()
        self.lock = threading.Lock()
        self.lookup_type = lookup_type
        self.file_path = file_path

        # Make an iterable object that contains URL paths
        # This can come from a file or from the pihole database
        if self.file_path is None:
            connection = sqlite3.connect('/etc/pihole/pihole-FTL.db')
            cursor = connection.cursor()
            iterable_object = []
            unique_urls = {}
            allurls = cursor.execute('select domain from queries order by domain ;')
            for tuple_ in allurls:
                if tuple_[0] not in unique_urls:
                    unique_urls[tuple_[0]] = ""
                    iterable_object.append(tuple_[0])
        else:
            # If a URL file is given, use this to determine which URLs to lookup for the database
            iterable_object = open(self.file_path, "r")

        threads = []
        if iterable_object is not None:
            # Given URLs to lookup, do so using concurrent nslookups
            for line in iterable_object:
                url = line.strip()
                if self.lookup_type is None:
                    threads.append(ConcurrentDig(url, self))
                else:
                    threads.append(ConcurrentNSLookup(url, self))
                try:
                    while threading.activeCount() > 12:
                        time.sleep(0.1)
                    threads[-1].start()
                except RuntimeError as error:
                    print("Runtime error:", error)
                    print("Running threads:", len(threads))
                    sys.exit(-1) # need to terminate, somethings not right
            for thread in threads:
                thread.join()
            print("Lookup performed on", len(threads), "urls")
        else:
            print("Something went very wrong in the database build")
            sys.exit(-1) # need to terminate, somethings not right


class ConcurrentNSLookup(threading.Thread):
    '''
    Concurret nslookup class - looks up one URL using nslookup
    '''
    def __init__(self, url, common_objects):
        '''
        Constructor
        '''
        super(ConcurrentNSLookup, self).__init__(args=(url,))
        self.command = "/usr/bin/nslookup"
        self.url_name = re.compile(r"^Name:")
        self.response = re.compile(r"^Address:[^\d]+(\d+\.\d+\.\d+.\d+)")
        self.common_objects = common_objects

    def run(self):
        '''
        Code to run when thread is started
        '''
        url = self._args[0]
        # run a subprocess that is a nslookup
        result = subprocess.run([self.command, url], stdout=subprocess.PIPE)
        paragraph = result.stdout.decode('utf-8')
        found_name = False
        # parse the reply, putting any found URL into the database
        for paragraph_line in paragraph.split("\n"):
            match = self.url_name.search(paragraph_line)
            if match:
                found_name = True
            else:
                if found_name:
                    match = self.response.search(paragraph_line)
                    if match:
                        ip_address = match.group(1)
                        self.common_objects.lock.acquire()
                        self.common_objects.url2ip[url] = ip_address
                        # Note, the below code may overwrite a url definition
                        self.common_objects.ip2url[ip_address] = url
                        self.common_objects.lock.release()

class ConcurrentDig(threading.Thread):
    '''
    Concurret dig class - looks up one URL using dig
    '''
    def __init__(self, url, common_objects):
        '''
        Constructor
        '''
        super(ConcurrentDig, self).__init__(args=(url,))
        self.command = "/usr/bin/dig"
        self.answer_section = re.compile(r"^;; ANSWER SECTION:")
        self.name_ip_pair = re.compile(r"^([^\s]+)\s+\d+\s+IN\s+[^\s]+\s+(\d+\.\d+\.\d+.\d+)")
        self.common_objects = common_objects

    def run(self):
        '''
        Code to run when thread is started
        '''
        url = self._args[0]
        # run a subprocess that is a nslookup
        result = subprocess.run(
            [self.command, "+noidnout", "+noidnin", url], stdout=subprocess.PIPE)
        paragraph = result.stdout.decode('utf-8')
        found_answer_section = False
        # parse the reply, putting any found URL into the database
        for paragraph_line in paragraph.split("\n"):
            match = self.answer_section.search(paragraph_line)
            if match:
                found_answer_section = True
            else:
                if found_answer_section:
                    match = self.name_ip_pair.search(paragraph_line)
                    if match:
                        found_url = match.group(1).rstrip('.')
                        ip_address = match.group(2)
                        self.common_objects.lock.acquire()
                        self.common_objects.url2ip[url] = ip_address
                        self.common_objects.ip2url[ip_address] = found_url
                        print(ip_address, found_url)
                        self.common_objects.lock.release()

def main():
    '''
    test driver & core database build method
    '''
    start_time = time.time()
    database = BuildUrlIpDb() #build via constructor
    database.dump_database()  #store on disk
    end_time = time.time()
    print("Processing took", end_time - start_time, "seconds")
if __name__ == '__main__':
    main()
