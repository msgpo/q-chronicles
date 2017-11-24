#!/usr/bin/env python
# ---------------------------------------------------------
# built for Q
# version: 0.0.1
# ---------------------------------------------------------
# code quality: none
# code level: below normie, i dont like python
# ---------------------------------------------------------
# dependencies:
#  - python 2.7.14+ (linux, mac)
#  - see imports (pip install ... or apt install ...)
# ---------------------------------------------------------

import json
import sys
import re
import urllib
import datetime
import os
import time
import urllib2,cookielib
import pytz
from HTMLParser import HTMLParser
from urlparse import urlparse
from os.path import splitext, basename
from collections import Counter

# commandline brabb
if len(sys.argv) != 3:
    print "Usage: %s [search.json] [fetch/load]" % sys.argv[0]
    sys.exit(0)

# unicode
def __unicode__(self):
   return unicode(self.some_field) or u''

# fetch from archive 4plebs
def process_4plebs_api(s,force=False,rt=False):
    my_file = s['file']
    fexists = False
    if os.path.exists(my_file):
        print "file:",my_file," already exists, ignoring"
        fexists = True

    if force:
        fexists = False

    if not fexists:
        print "fetching data for file:",my_file
        # sleep for plebs!
        time.sleep(1)
        hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
               'Accept-Encoding': 'none',
               'Accept-Language': 'en-US,en;q=0.8',
               'Connection': 'keep-alive'}
        req = urllib2.Request(s['url'], headers=hdr)
        try:
            page = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            print e.fp.read()

        # read url content
        content = page.read()
        fh = open(my_file, 'w')
        fh.write(content)
        fh.close()
        # sleep again to avoid ban
        print "sleeping ..."
        time.sleep(8)
        # return data?
        if rt:
            return content


# =======================
# Main
# =======================
htmlparser = HTMLParser()

# read given servistate file (see chrome plugin how to)
data = json.load(open(sys.argv[1]))
local= sys.argv[2]

# check if search file
try:
    check = data["meta"]
    slist = data["search"]
except KeyError:
    sys.exit("error, json not searchlist format")

# init
searchDict   = slist
searchList   = []
threads      = []  # just bunch of ints
postDict     = []

# iterate plebs urls and call api if no file(s)
for q in searchDict:
    if q["ident"] == "tripcode":
        s           = { "url": '', "file": '' }
        s['url']    = q["url"]
        s['file']   = "4plebs/searchresult-tripcode-page-1.json"
        # call api and save always
        if local == 'fetch':
            dt = process_4plebs_api(s,True,True)
            rd = json.load(open(s['file']))

        if local == 'load':
            rd = json.load(open(s['file']))

        testlen = len(rd["0"]["posts"])
        checklen= int(rd["meta"]["total_found"])

        if checklen > testlen:
            pages = int(round((checklen/testlen)+0.5))
            print "pagination detected, ",pages," used"
            # refetch
            for n in xrange(1, pages+1):
                s['url']    = q["url"] + "&page=" + str(n)
                s['file']   = "4plebs/searchresult-tripcode-page-"+str(n)+".json"
                if local == 'fetch':
                    dt = process_4plebs_api(s,True,True)
                    rd = json.load(open(s['file']))

                if local == 'load':
                    print "loading:",s['file']
                    rd = json.load(open(s['file']))

                # build result
                for post in rd["0"]["posts"]:
                    postDict.append(post)
        else:
            postDict = rd["0"]["posts"]

#        sys.exit()

        # parse return data and save iterated result
        for r in postDict:
            postnum   = r['num']
            threadnum = r['thread_num']
            posterhash= r['poster_hash']
            thread_file= "compiled/json/threads/thread_" + threadnum + ".json"
            post_file= "compiled/json/posts/post_" + postnum + ".json"

            #check if post json exists
            if not os.path.exists(post_file):
                print "file:",post_file," does not exists, fetching post"
                s['url']  = "http://archive.4plebs.org/_/api/chan/post/?board=pol&num=" + postnum
                s['file'] = post_file
                process_4plebs_api(s)
            else:
                print "file:",post_file," exists, ok"

            #check if thread json exists
            if not os.path.exists(thread_file):
                print "file:",thread_file," does not exists, fetching thread"
                s['url']  = "http://archive.4plebs.org/_/api/chan/thread/?board=pol&num=" + threadnum
                s['file'] = thread_file
                process_4plebs_api(s)
            else:
                print "file:",thread_file," exists, ok"
# saged
