#!/usr/bin/env python3
'''
Domain Name Utilities - convert domain name to IP and IP to domain name
'''
import re
import os
import pickle
import sqlite3
import subprocess
import threading
import time

class lookup_url_ip(object):
    '''
    Base class of URL / IP database
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.URL2IP = {}
        self.IP2URL = {}
        try:
            # If directed to use the preprocessed database, load them
            fileHandle = open("URL2IP.db", "rb")
            self.URL2IP = pickle.load(fileHandle)
            fileHandle.close()
            fileHandle = open("IP2URL.db", "rb")
            self.IP2URL = pickle.load(fileHandle)
            fileHandle.close()
        except FileNotFoundError:
            print("Using empty database as a start")

    def dumpDatabase(self):
        '''
        Method to dump the conversion databases
        '''
        print(self.URL2IP, self.IP2URL)

    def anotateIP(self, ip):
        '''
        Using an IP, anotate it if possible
        '''
        if ip in self.IP2URL:
            ip = ip + " (" + self.IP2URL[ip] +")"
        return ip

class build_url_ip_db(lookup_url_ip):
    '''
    Class that handles creation and update of the URL / IP database
    '''
    def __init__(self, lookup_type=None, file_path=None):
        '''
        Constructor
        '''
        super(build_url_ip_db, self).__init__()
        self.lock = threading.Lock()
        self.lookup_type = lookup_type
        self.file_path = file_path

        #Make an iterable object that contains URL paths, this can come from a file or from the pihole database
        if self.file_path is None:
            connection = sqlite3.connect('/etc/pihole/pihole-FTL.db')
            cursor = connection.cursor()
            iterableObject = []
            uniqueURLs = {}
            allurls = cursor.execute('select domain from queries order by domain ;')
            for tuple_ in allurls:
                if tuple_[0] not in uniqueURLs:
                    uniqueURLs[tuple_[0]] = ""
                    iterableObject.append(tuple_[0])
        else:
            # If a URL file is given, use this to determine which URLs to lookup for the database
            iterableObject = open(self.file_path, "r")

        threads = []
        if iterableObject is not None:
            # Given URLs to lookup, do so using concurrent nslookups
            for line in iterableObject:
                url = line.strip()
                if self.lookup_type is None:
                    threads.append(concurrentDig(url, self))
                else:
                    threads.append(concurrentNSLookup(url, self))
                threads[-1].start()
            for thread in threads:
                thread.join()
            print("Lookup performed on", len(threads), "urls")
            fileHandle = open("URL2IP.db", "wb")
            pickle.dump(self.URL2IP, fileHandle)
            fileHandle.close()
            fileHandle = open("IP2URL.db", "wb")
            pickle.dump(self.IP2URL, fileHandle)
            fileHandle.close()
        else:
            print("Something went very wrong in the database build")


class concurrentNSLookup(threading.Thread):
    '''
    Concurret nslookup class - looks up one URL using nslookup
    '''
    def __init__(self, url, commonObjects):
        '''
        Constructor
        '''
        super(concurrentNSLookup, self).__init__(args=(url,))
        self.command = "/usr/bin/nslookup"
        self.URLName = re.compile(r"^Name:")
        self.response = re.compile(r"^Address:[^\d]+(\d+\.\d+\.\d+.\d+)")
        self.commonObjects = commonObjects

    def run(self):
        '''
        Code to run when thread is started
        '''
        url = self._args[0]
        # run a subprocess that is a nslookup
        result = subprocess.run([self.command, url], stdout=subprocess.PIPE)
        paragraph = result.stdout.decode('utf-8')
        foundName = False
        # parse the reply, putting any found URL into the database
        for paragraphLine in paragraph.split("\n"):
            match = self.URLName.search(paragraphLine)
            if match:
                foundName = True
            else:
                if foundName:
                    match = self.response.search(paragraphLine)
                    if match:
                        ip = match.group(1)
                        self.commonObjects.lock.acquire()
                        self.commonObjects.URL2IP[url] = ip
                        # Note, the below code may overwrite a url definition
                        self.commonObjects.IP2URL[ip] = url
                        self.commonObjects.lock.release()

class concurrentDig(threading.Thread):
    '''
    Concurret dig class - looks up one URL using dig
    '''
    def __init__(self, url, commonObjects):
        '''
        Constructor
        '''
        super(concurrentDig, self).__init__(args=(url,))
        self.command = "/usr/bin/dig"
        self.answer_section = re.compile(r"^;; ANSWER SECTION:")
        self.name_ip_pair = re.compile(r"^([^\s]+)\s+\d+\s+IN\s+[^\s]+\s+(\d+\.\d+\.\d+.\d+)")
        self.commonObjects = commonObjects

    def run(self):
        '''
        Code to run when thread is started
        '''
        url = self._args[0]
        # run a subprocess that is a nslookup
        result = subprocess.run([self.command, url], stdout=subprocess.PIPE)
        paragraph = result.stdout.decode('utf-8')
        found_answer_section = False
        # parse the reply, putting any found URL into the database
        for paragraphLine in paragraph.split("\n"):
            match = self.answer_section.search(paragraphLine)
            if match:
                found_answer_section = True
            else:
                if found_answer_section:
                    match = self.name_ip_pair.search(paragraphLine)
                    if match:
                        found_url = match.group(1).rstrip('.')
                        ip = match.group(2)
                        self.commonObjects.lock.acquire()
                        self.commonObjects.URL2IP[url] = ip
                        self.commonObjects.IP2URL[ip] = found_url
                        print(ip, found_url)
                        self.commonObjects.lock.release()

def main():
    '''
    test driver
    '''
    start_time = time.time()
    database = build_url_ip_db()
    end_time = time.time()
    print("Processing took", end_time - start_time, "seconds")
if __name__ == '__main__':
    main()
