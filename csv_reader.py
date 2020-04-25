#!/usr/bin/env python

import csv
import re
#from splinter import Browser
import requests
import os
import urllib.request
import twint
import threading
import json
import m3u8
import urllib.parse
import ffmpeg
import shutil
from pathlib import Path


def thread_task (file_to_read, start, end, output_dir):
    line_val = 0
    print (start)
    print (end)
    with open (file_to_read, newline = '') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
                if (line_val >= start and line_val < end):
                        regex_find = re.search("pic\.twitter\.com\/([a-z]|[A-Z]|[0-9])+", row['tweet'])
                        if (regex_find and row.get('video') == '1'):
                                r = requests.get('https://' + regex_find.group())
                                print (str(threading.get_ident()) + " downloading " + r.url)
                                os.system("python3 twitter-dl.py " + r.url + " -o  " + output_dir)
                                #print ("downloading " + r.url)
                                #twitter_dl = TwitterDownloader(r.url, output_dir, 0)
                                #twitter_dl.download()

                        elif (row.get('photos') != "[]"):
                                new_help = row['photos'].replace("[","")
                                new_help = new_help.replace("]", "")
                                new_help = new_help.replace(" ", "")
                                new_help = new_help.replace("'","")
                                pic_urls = str(new_help).split(',')
                                i = 0
                                for x in pic_urls:
                                        r = requests.get(x)
                                        reged_id = re.search("([A-Z]|[a-z]|[0-9]|-|_)+\.(jpg|png)",x)
                                        reg_string_split = reged_id.group().split(".")
                                        file_loc = '/home/scraper/twint/output/' + reg_string_split[0]

                                        with open(file_loc, 'wb') as f:
                                                f.write(r.content)
                                                f.flush()
                                                f.close()
                                        i += 1
                        line_val += 1

if __name__ == "__main__":

    c = twint.Config()
    c.Output = 'hohoro_4_23.csv'
    #c.Username = "adhd_superpower"
    #c.Output = input("What would you like to name the file (no file extension needed): ")
    #output_dir = input("Where would you like to save the pics + vids to: ")
    #replace below line when code is proven to work
    output_dir = './output'
    #c.Output = c.Output + ".csv"
    #c.Store_csv = True
    #twint.run.Favorites(c)
    
    csv_row_number = 0
    with open ('hohoro_4_23.csv', newline = '') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            csv_row_number += 1

        print (csv_row_number)

    #make this enterable at a later date
    threads_to_use = 4
    num_per_thread = (int)(csv_row_number/threads_to_use)
    thread_list = list()
    value_acc = 0
    
    for x in range(threads_to_use):
        if (x != threads_to_use - 1):
            y = threading.Thread(target = thread_task, args = (c.Output, value_acc, value_acc + num_per_thread, output_dir ))
            thread_list.append(y)
            y.start()
            value_acc += num_per_thread
        else:
            y = threading.Thread(target = thread_task, args = (c.Output, value_acc, csv_row_number, output_dir))
            thread_list.append(y)
            y.start()


    for thread in enumerate(thread_list):
        thread.join()
    

