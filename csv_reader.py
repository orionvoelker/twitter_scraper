#!/usr/bin/env python

import csv
import re
#from splinter import Browser
import os
import os.path
from os import path
import urllib.request
import twint
import threading
import json
import m3u8
import urllib.parse
import ffmpeg
import shutil
from pathlib import Path
import argparse
import requests
from multiprocessing import Process

def thread_task (file_to_read, start, end, output_dir):
    line_val = 0
    print (str(os.getpid()) + " is here")
    with open (file_to_read, newline = '') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if (line_val >= start and line_val < end):
                regex_find = re.search("pic\.twitter\.com\/([a-z]|[A-Z]|[0-9])+", row['tweet'])
                print (str(os.getpid()) + " freezes here")
                if (regex_find and row.get('video') == '1'):
                    video_player_prefix = 'https://twitter.com/i/videos/tweet/'
                    video_api = 'https://api.twitter.com/1.1/videos/tweet/config/'
                    tweet_data = {}
                    r = requests.get('https://' + regex_find.group())
                    print (str(os.getpid()) + " downloading " + r.url)
                    #os.system("python3 twitter-dl.py " + r.url + " -o  " + output_dir)
                    #parser = argparse.ArgumentParser()
                    #parser.add_argument('tweet_url', help = 'The video URL on Twitter (https://twitter.com/<user>/status/<id>).')
                    #parser.add_argument('-o', '--output', dest = 'output', default = './output', help = 'The directory to output to. The structure will be: <output>/<user>/<id>.')
                    #parser.add_argument('-d', '--debug', default = 0, action = 'count', dest = 'debug', help = 'Debug. Add more to print out response bodies (maximum 2).')
                    
                    #args = parser.parse_args()
                    #twitter_dl = TwitterDownloader(args.tweet_url, args.output, args.debug)
                    tweet_url = r.url
                    output_dir = output_dir
                    
                    tweet_data['tweet_url'] = tweet_url.split('?', 1)[0]
                    tweet_data['user'] = tweet_data['tweet_url'].split('/')[3]
                    tweet_data['id'] = tweet_data['tweet_url'].split('/')[5]
                    
                    downloaded_video_names = []
                    
                    output_path = Path(output_dir)
                    storage_dir = output_path #/ self.tweet_data['user'] / self.tweet_data['id']
                    Path.mkdir(storage_dir, parents = True, exist_ok = True)
                    storage = str(storage_dir)
                    req = requests.Session()
                    
                    video_player_url = video_player_prefix + tweet_data['id']
                    video_player_response = req.get(video_player_url).text
                    
                    js_file_url  = re.findall('src="(.*js)', video_player_response)[0]
                    js_file_response = req.get(js_file_url).text
                    
                    bearer_token_pattern = re.compile('Bearer ([a-zA-Z0-9%-])+')
                    bearer_token = bearer_token_pattern.search(js_file_response)
                    bearer_token = bearer_token.group(0)
                    req.headers.update({'Authorization': bearer_token})
                    
                    res = req.post("https://api.twitter.com/1.1/guest/activate.json")
                    res_json = json.loads(res.text)
                    req.headers.update({'x-guest-token': res_json.get('guest_token')})
                    
                    token = bearer_token
                    
                    player_config_req = req.get(video_api + tweet_data['id'] + '.json')
                    
                    player_config = json.loads(player_config_req.text)

                    if 'errors' not in player_config:
                        m3u8_url = player_config['track']['playbackUrl']

                    else:
                        print('[-] Rate limit exceeded. Could not recover. Try again later.')
                        sys.exit(1)
                        
                    # Get m3u8
                    m3u8_response = req.get(m3u8_url)
                    
                    m3u8_url_parse = urllib.parse.urlparse(m3u8_url)
                    video_host = m3u8_url_parse.scheme + '://' + m3u8_url_parse.hostname
                    
                    m3u8_parse = m3u8.loads(m3u8_response.text)
                    host_video = video_host
                    playlist = m3u8_parse
                    
                    print('[+] Multiple resolutions found.')

                    for plist in playlist.playlists:
                        resolution = str(plist.stream_info.resolution[0]) + 'x' + str(plist.stream_info.resolution[1])
                        resolution_file = Path(storage) / Path(resolution + '_' + tweet_data['id'] + '_' + '.mp4')
                        downloaded_video_names.append(resolution_file)
                        print('[+] Downloading ' + resolution)

                        playlist_url = video_host + plist.uri
                        
                        ts_m3u8_response = req.get(playlist_url, headers = {'Authorization': None})
                        ts_m3u8_parse = m3u8.loads(ts_m3u8_response.text)
                        
                        ts_list = []
                        ts_full_file_list = []

                        
                        for ts_uri in ts_m3u8_parse.segments.uri:
                            #ts_list.append(video_host + ts_uri)
                            
                            ts_file = requests.get(video_host + ts_uri)
                            fname = ts_uri.split('/')[-1]
                            ts_path = Path(storage) / Path(fname)
                            ts_list.append(ts_path)
                            
                            ts_path.write_bytes(ts_file.content)

                        ts_full_file = Path(storage) / Path(resolution + '.ts')
                        ts_full_file = str(ts_full_file)
                        ts_full_file_list.append(ts_full_file)
                        
                        # Shamelessly taken from https://stackoverflow.com/questions/13613336/python-concatenate-text-files/27077437#27077437
                        with open(str(ts_full_file), 'wb') as wfd:
                            for f in ts_list:
                                with open(f, 'rb') as fd:
                                    shutil.copyfileobj(fd, wfd, 1024 * 1024 * 10)


                            for ts in ts_full_file_list:
                                print('\t[*] Doing the magic ...')
                                ffmpeg\
                                    .input(ts)\
                                    .output(str(resolution_file), acodec = 'copy', vcodec = 'libx264', format = 'mp4', loglevel = 'error')\
                                    .overwrite_output()\
                                    .run()

                            #print('\t[+] Doing cleanup')
                            
                            for ts in ts_list:
                                p = Path(ts)
                                p.unlink()

                            for ts in ts_full_file_list:
                                p = Path(ts)
                                p.unlink()
                        # else:
                        #print('[-] Sorry, single resolution video download is not yet implemented. Please submit a bug report with the link to the tweet.')
                        
                    for x in range(0, len(downloaded_video_names)-1):
                        os.system("sudo rm " + str(downloaded_video_names[x]))
                            
                            
                elif (row.get('photos') != "[]"):
                    new_help = row['photos'].replace("[","")
                    new_help = new_help.replace("]", "")
                    new_help = new_help.replace(" ", "")
                    new_help = new_help.replace("'","")
                    pic_urls = str(new_help).split(',')
                   # i = 0
                    for x in pic_urls:
                        r2 = requests.get(x)
                        reged_id = re.search("([A-Z]|[a-z]|[0-9]|-|_)+\.(jpg|png)",x)
                        print (str(os.getpid()) + " downloading " + r2.url)
                        reg_string_split = reged_id.group().split(".")
                        file_loc = './output/' + reg_string_split[0]
                        
                        with open(file_loc, 'wb') as f:
                            f.write(r2.content)
                            f.flush()
                            f.close()
                        #i += 1
                line_val += 1

def main():

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
            y = Process(target = thread_task,  args = (c.Output, value_acc, value_acc + num_per_thread, output_dir ))
            thread_list.append(y)
            y.start()
            value_acc += num_per_thread
        else:
            y = Process(target = thread_task,  args = (c.Output, value_acc, csv_row_number, output_dir))
            thread_list.append(y)
            y.start()
            
    for x in range(threads_to_use):
        thread_list[x].join()

    
if __name__ == "__main__":
    main()
