#!/usr/bin/env python
# ---------------------------------------------------------
# built for Q
# version: 0.0.9
# ---------------------------------------------------------
# code quality: none
# code level: below normie, i dont like python
# ---------------------------------------------------------
# dependencies:
#  - python 2.7.14+ (linux, mac)
#  - see imports (pip install ... or apt install ...)
# ---------------------------------------------------------
# quick rundown:
# - ugly compiled with stackoverflow copy paste
# - requires servistat formatted json/project file
# - import servistate-current.json (symlink!) into your chrome (extension needed)
# - clone a request if new Q posts appear with specific userID
# - test api request and export servistate file, remove & create symlink pointing to new file
# - execute tools/convert4plebs.py [fetch|convert] and look for errors or something
# - update timeline_daily.html's for new content if wanted
# - q.json is pretty large, rendering could take a while, mozilla quantum (Q!!!) is pretty neat
# ---------------------------------------------------------
# offline browsing
# - fagfox is fine
# - chrome (macos) eg. start with open /Applications/Google\ Chrome.app --args --allow-file-access-from-files
# - linux same
# - idK about windoze
# ---------------------------------------------------------

import json
import sys
import re      # venti b00bs
import urllib
import datetime
import os
import time
import urllib2,cookielib
import pytz
from HTMLParser import HTMLParser
from urlparse import urlparse
from os.path import splitext, basename
from BeautifulSoup import BeautifulSoup

# commandline brabb
if len(sys.argv) != 2:
    print "Usage: %s [fetch|convert]" % sys.argv[0]
    sys.exit(0)

# unicode
def __unicode__(self):
   return unicode(self.some_field) or u''

# fetch image/media to filecache
def process_4plebs_media(s):
    disassembled = urlparse(s)
    filename, file_ext = splitext(basename(disassembled.path))
    cachefile =  "imgcache/" + filename + file_ext
    d={"file": "compiled/" + cachefile, "url": s}
    process_4plebs_api(d)
    return cachefile

# fetch from archive 4plebs
def process_4plebs_api(s,force=False):
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
        content = page.read()
        fh = open(my_file, 'w')
        fh.write(content)
        fh.close()
        # sleep again to avoid ban
        time.sleep(8)

def process_4plebs_timestamp(t,msoffset):
    # get time in UTC
    utc_dt = datetime.datetime.utcfromtimestamp(t).replace(tzinfo=pytz.utc)

    # convert it to tz
    tz = pytz.timezone('America/New_York')
    dt = utc_dt.astimezone(tz)
    raw_utc_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')

    # create dates
    sdate               = { "year": "", "month": "", "day": "", "hour": "", "minute": "", "second": "", "millisecond": "", "format": "" }
    sdate['year']       = dt.strftime('%Y')
    sdate['month']      = dt.strftime('%m')
    sdate['day']        = dt.strftime('%d')
    sdate['hour']       = dt.strftime('%H')
    sdate['minute']     = dt.strftime('%M')
    sdate['second']     = dt.strftime('%S')
    sdate['_identdate'] = dt.strftime('%Y%m%d')
    sdate['millisecond']= msoffset
    sdate['format']     = "'<small>'mmmm d',' yyyy'</small>' - HH:MM:ss TT"
    sdate['raw_utc']    = raw_utc_timestamp

    return sdate

# single news
def process_news_post(p):
    # init
    r  = { "headline": "", "text": "" }
    rd = {"start_date": {}, "text": {} }
    pm = { "url": "", "caption": "", "thumbnail": "", "link": "", "link_target": "_blank", "credit": "" }
    post_timestamp  = p['timestamp']
    # get time in UTC
    post_startDate    = process_4plebs_timestamp(post_timestamp,"02")
    try:
        post_timestamp_end = p['timestamp_end']
        rd['end_date'] = process_4plebs_timestamp(p['timestamp_end'],"00")
    except KeyError:
        pass

    post_title        = p['title']
    post_text         = p['text'] + "<br><br>" + "<i>Source: " + p['src'] + "</i><br>"
    post_text        += p['url']
    # event media
    try:
        pm['url']   = p['media_url']
        rd['media'] = pm
    except KeyError:
        pass
    #post_media['link']= "_link "# p['url']
    # r
    r['headline']     = post_title
    r['text']         = post_text

    # build return data
    rd['text']          = r
    rd['start_date']    = post_startDate
    rd['_identdate']    = post_startDate['_identdate']
    return rd

def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

# process single post
def process_4plebs_post(p,rt):
    # init
    r               = { "headline": "", "text": "" }
    post_num        = p['num']
    post_timestamp  = int(p['timestamp'])
    post_excerpt    = ""
    post_trip       = ""
    post_title      = ""
    post_media      = ""
    post_news       = ""
    post_news_head  = ""
    post_backlink   = ""

    # fetch post and thread if not exist
    urL_archive_thread  = "http://archive.4plebs.org/pol/thread/" + p['thread_num']
    url_archive_post    = "http://archive.4plebs.org/pol/thread/" + p['thread_num'] + "/#" + post_num
    url_json_call       = "http://archive.4plebs.org/_/api/chan/post/?board=pol&num=" + post_num
    url_json_local      = "json/posts/post_" + post_num + ".json"

    #check if post json exists
    s         = { "url": '', "file": '' }
    s['url']  = url_json_call
    s['file'] = "compiled/" + url_json_local
    process_4plebs_api(s)


    # get time in UTC
    post_startDate    = process_4plebs_timestamp(post_timestamp,"02")
    raw_utc_timestamp = post_startDate['raw_utc']

    # use raw comment
    post_comment_raw = p['comment']


    # is comment?
    if post_comment_raw and len(post_comment_raw) >= 1:
        post_comment  = htmlparser.unescape(post_comment_raw)
        clean_html    = cleanhtml(post_comment)
        #clean_html    = cleanhtml(post_comment_raw)
        clean_html    = clean_html.replace("\n"," ")
        # build excerpt (not used now)
        #if len(clean_html) >= 50:
        #    post_excerpt     = post_comment[:50]
        #else:
        #    post_excerpt     = post_comment[:len(post_comment_raw)-1]

        #pattern = "\.(?P<sentence>.*?(\?).*?)\."
        #match = re.search(pattern, clean_html)
        #if match != None:
        #    sentence = match.group("sentence")
        #    print "sentence:",sentence
        datas = clean_html.split()[:4]
        print len(datas)
        if len(datas) >= 1:
            post_excerpt = datas[0] + " "
        if len(datas) >= 2:
            post_excerpt += datas[1] + " "
        if len(datas) >= 3:
            post_excerpt += datas[2] + " "
        if len(datas) >= 4:
            post_excerpt += datas[3] + " "
        post_excerpt += "..."
        # html linebreaks
        post_comment     = post_comment.replace("\n","<br>")
    else:
        post_comment     = ""

    # post tripper
    if p['trip']:
        post_trip = ' ' +  p['trip']

    # post title
    if p['title']:
        post_title = p['title'] # op faggot
    else:
        post_title = p['name']  # user faggot

    # build some html
    poster_country   = p["poster_country"]
    post_country     = '<span class="flag flag-'+poster_country.lower()+'"></span>'
    #post_headline    = '<div class="4plebs_headline">'
    #post_headline   += p['name'] + ' ' + post_trip + '(ID: ' + p['poster_hash'] + ') ' + p['fourchan_date'] + ' No.' + post_num
    #post_headline   += '</div>'
    # add to html return
    post_headline  = '<div class="4plebs_headline">' + p['name'] + ' ' + post_trip + ' (ID: ' + p['poster_hash'] + ') ' + ' No.' + post_num + ' ' + post_country + '</div>'
    post_comment  = post_headline + post_comment


    r['headline'] = post_excerpt #post_trip + ' ' + p['fourchan_date']

    # process media if set
    if p['media']:
        media           = p['media']
        media_link      = urllib.unquote(urllib.unquote(media['media_link']))
        thumb_link      = urllib.unquote(urllib.unquote(media['thumb_link']))
        preview_w       = urllib.unquote(urllib.unquote(media['preview_w']))
        preview_h       = urllib.unquote(urllib.unquote(media['preview_h']))
        media_filename  = urllib.unquote(urllib.unquote(media['media_filename']))
        # grab files for offline caching
        cachefile_url   = process_4plebs_media(media_link)
        cachethumb_url  = process_4plebs_media(thumb_link)
        # html (inline)
        post_media_inl  = '<div class="media-inline"><a href="'+cachefile_url+'" target="_blank"><img src="'+cachethumb_url+'" width="'+preview_w+'" height="'+preview_h+'" title="'+media_filename+'"></a></div>'
        # event media
        post_media      = { "url": "", "caption": "", "thumbnail": "", "link": "", "link_target": "_blank", "credit": "" }
        post_media['url'] = cachethumb_url
        post_media['thumbnail'] = cachethumb_url
        post_media['link'] = cachefile_url
        post_media['caption'] = media_filename

    bldt = ""
    try:
        isbl = p['backlink']
        bldt = render_backlink(isbl)
    except KeyError:
        pass
    if bldt:
        # post_backlink
        post_backlink = bldt

    # build context
    post_srccontext  = '<div class="4plebs_context_' + post_num + ' ">'
    post_srccontext += '<strong>Timestamp:</strong> '+ str(post_timestamp) + ' -- ' + raw_utc_timestamp +'<br>'
    post_srccontext += '<strong>Archive:</strong>'
    post_srccontext += '&nbsp;&raquo;<a class="tl-makelink" onclick="void(0)" target="_blank" href="' + url_json_local + '">JSON</a><br>'
    post_srccontext += '<strong>Online:</strong>'
    post_srccontext += '&nbsp;&raquo;<a class="tl-makelink" onclick="void(0)" target="_blank" href="' + url_archive_post + '">Post</a>'
    post_srccontext += '&nbsp;&raquo;<a class="tl-makelink" onclick="void(0)" target="_blank" href="' + urL_archive_thread + '">Thread</a>'
    post_srccontext += '&nbsp;&raquo;<a class="tl-makelink" onclick="void(0)" target="_blank" href="' + url_json_call + '">JSON</a>'
    post_srccontext += '</div>'

    # news context (excerpt)
    post_news_head = post_title
    post_news   = post_comment
    post_news  += '<br><br>&raquo; <a class="tl-makelink" onclick="void(0)" target="_blank" href="' + url_archive_post + '">Post</a>'
    post_news  += '  &raquo; <a class="tl-makelink" onclick="void(0)" target="_blank" href="' + urL_archive_thread + '">Thread</a>'

    # build html body
    post_commentbody   = '<div class="4plebs_contentbody_' + post_num + ' ">'
    post_commentbody  += post_backlink + post_comment
    post_commentbody  += '</div>'
    # post_media_inl
    if rt == "detail":
        r['text'] = post_commentbody + "<br>" + post_srccontext
    elif rt == "news":
        r['text'] = post_news
        r['headline'] = post_news_head
    else:
        r['text'] = post_commentbody + "<br>" + post_srccontext

    # build return data
    rd = {"start_date": {}, "text": {}, "media": {} }
    rd['text']          = r
    rd['start_date']    = post_startDate
    rd['media']         = post_media
    rd['_identdate']    = post_startDate['_identdate']
    rd['post_num']      = post_num
    rd['thread_num']    = p['thread_num']
    #d['background'] = {
    #                "color": "#202020",
    #                "opacity": 100,
    #                "url": ""
    #            }
    #d['end_date'] = post_endDate
    return rd


# process single thread
def process_4plebs_thread(s):
    # init
    s         = { "url": '', "file": '' }
    s['url']  = "http://archive.4plebs.org/_/api/chan/thread/?board=pol&num=" + str(thread)
    s['file'] = "compiled/json/threads/thread_" + str(thread) + ".json"
    # call api
    process_4plebs_api(s)
    # reload from local and process thread from to information
    data = json.load(open(s['file']))
    te   = { "start_date": {}, "end_date": {}, "media": "", "text": {} , "group": "CBTS"}
    re   = { "headline": "", "text": "" }
    # ...
    op = ""

    thread_start = ''
    thread_end   = ''
    # get op
    if data[str(thread)]["op"]:
        op = data[str(thread)]["op"]
        thread_start = op["timestamp"]
        # process t
        te['start_date'] = process_4plebs_timestamp(int(thread_start),"00")
    else:
        print "thread OP NOT okay!"

    # find last post entry timestamp
    if data[str(thread)]["posts"]:
        posts = data[str(thread)]["posts"]
        posts_last = sorted(posts.keys())[-1]
        thread_end = data[str(thread)]["posts"][str(posts_last)]["timestamp"]
        te['end_date'] = process_4plebs_timestamp(int(thread_end),"00")

    # build some event entry context
    te_headline = ""
    if op["title"]:
        te_headline = htmlparser.unescape(op["title"])
    else:
        # faggot op set no title!
        te_headline = "Thread: " + str(thread)

    # process media if set
    op_media = ""
    if op["media"]:
        media           = op['media']
        media_link      = urllib.unquote(urllib.unquote(media['media_link']))
        thumb_link      = urllib.unquote(urllib.unquote(media['thumb_link']))
        preview_w       = urllib.unquote(urllib.unquote(media['preview_w']))
        preview_h       = urllib.unquote(urllib.unquote(media['preview_h']))
        media_filename  = urllib.unquote(urllib.unquote(media['media_filename']))
        # grab files for offline caching
        cachefile_url   = process_4plebs_media(media_link)
        cachethumb_url  = process_4plebs_media(thumb_link)
        # event media
        op_media      = { "url": "", "caption": "", "thumbnail": "", "link": "", "link_target": "_blank", "credit": "" }
        op_media['url'] = cachethumb_url
        op_media['thumbnail'] = cachethumb_url
        op_media['link'] = cachefile_url
        op_media['caption'] = media_filename

    # build context
    # post tripper
    op_trip = ''
    if op['trip']:
        op_trip = op['trip']
    urL_archive_thread  = "http://archive.4plebs.org/pol/thread/" + str(thread)
    url_json_call       = "http://archive.4plebs.org/_/api/chan/thread/?board=pol&num=" + str(thread)
    url_json_local      = "json/threads/thread_" + str(thread) + ".json"
    post_srccontext     = '<div class="tl-media"><div class="tl-media-content-container tl-media-content-container-text"><div class="tl-media-content">'
    post_srccontext    += '<div class="tl-media-item tl-media-wikipedia 4plebs_threadcontext_' + str(thread) + ' ">'

#    post_srccontext    += '<strong>Archive-Info:</strong><br>'
#    post_srccontext    += '  &nbsp;' + op['name'] + ' ' + op_trip + '(ID: ' + op['poster_hash'] + ') ' + op['fourchan_date'] + ' No.' + op['thread_num'] + '<br>'
#    post_srccontext    += '  &nbsp;Unix Timestamp: '+ str(thread_start) +'<br>'
#    post_srccontext    += '  &nbsp;DateTime: '+ te['start_date']['raw_utc'] +'<br>'
#    post_srccontext    += '  &nbsp;JSON:   <a class="tl-makelink" onclick="void(0)" target="_blank" href="' + url_json_local + '">' + url_json_local + '</a><br>'
#    post_srccontext    += '<strong>Online:</strong><br>'
#    post_srccontext    += '  &nbsp;Thread: <a class="tl-makelink" onclick="void(0)" target="_blank" href="' + urL_archive_thread + '">' + urL_archive_thread + '</a><br>'
#    post_srccontext    += '  &nbsp;JSON:   <a class="tl-makelink" onclick="void(0)" target="_blank" href="' + url_json_call + '">' + url_json_call + '</a><br>'

    post_srccontext += '<strong>Timestamp:</strong> '+ str(thread_start) + ' -- ' + te['start_date']['raw_utc'] +'<br>'
    post_srccontext += '<strong>Archive:</strong>'
    post_srccontext += '&nbsp;&raquo;<a class="tl-makelink" onclick="void(0)" target="_blank" href="' + url_json_local + '">JSON</a><br>'
    post_srccontext += '<strong>Online:</strong>'
    post_srccontext += '&nbsp;&raquo;<a class="tl-makelink" onclick="void(0)" target="_blank" href="' + urL_archive_thread + '">Thread</a>'
    post_srccontext += '&nbsp;&raquo;<a class="tl-makelink" onclick="void(0)" target="_blank" href="' + url_json_call + '">JSON</a>'

    post_srccontext    += '</div></div></div></div>'


    # build context


    # text object in text
    re['headline']  = te_headline
    re['text']      = post_srccontext

    # add to event
    te['background']= {
                    #"color": "#d0d0d5",
                    #"opacity": 50,
                    "url": "img/cbts2.jpg"
    }
    te['media']     = op_media
    te['text']      = re
    te['thread_ident'] = thread

    return te

def render_backlink(s):
    # load json
    p = json.load(open("compiled/json/posts/post_" + s + ".json"))
    post_comment_raw = p["comment"]
    post_media_inl   = ""
    if post_comment_raw and len(post_comment_raw) >= 1:
        post_comment = htmlparser.unescape(p["comment"])
        post_comment = post_comment.replace("\n","<br>")
    else:
        post_comment = ""

    # post tripper
    post_trip = ""
    post_num  = p["num"]
    if p['trip']:
        post_trip = ' ' +  p['trip']

    # post title
    if p['title']:
        post_title = p['title'] # op faggot
    else:
        post_title = p['name']  # user faggot

    # build some html
    print post_num
    poster_country   = p["poster_country"]
    poster_troll_country   = p["troll_country_code"]
    if poster_country:
        post_country     = '<span class="flag flag-'+poster_country.lower()+'"></span>'
    else:
        # try troll country
        if poster_troll_country:
            post_country = '<span class="flag flag-'+poster_troll_country.lower()+'"></span>'
        else:
            post_country = '<span class="flag flag-none"></span>'

    post_headline    = '<div class="4plebs_headline">' + p['name'] + ' ' + post_trip + ' (ID: ' + p['poster_hash'] + ') ' + ' No.' + post_num + ' ' + post_country + '</div>'

    # process media if set
    if p['media']:
        media           = p['media']
        media_link      = urllib.unquote(urllib.unquote(media['media_link']))
        thumb_link      = urllib.unquote(urllib.unquote(media['thumb_link']))
        preview_w       = urllib.unquote(urllib.unquote(media['preview_w']))
        preview_h       = urllib.unquote(urllib.unquote(media['preview_h']))
        media_filename  = urllib.unquote(urllib.unquote(media['media_filename']))
        # grab files for offline caching
        cachefile_url   = process_4plebs_media(media_link)
        cachethumb_url  = process_4plebs_media(thumb_link)
        # html (inline)
        post_media_inl  = '<div class="media-inline"><a href="'+cachefile_url+'" target="_blank"><img src="'+cachethumb_url+'" width="'+preview_w+'" height="'+preview_h+'" title="'+media_filename+'"></a></div>'

    post_srccontext  = '<div class="4plebs_backlink_' + s + ' ">'
    post_srccontext += post_headline + post_media_inl + post_comment
    post_srccontext += '</div>'
    return post_srccontext


# =======================
# Main
# =======================
htmlparser = HTMLParser()

# read given servistate file (see chrome plugin how to)
action = sys.argv[1]
servistate_file = "data/servistate-current.json"
#search_file     = "data/searchresult-tripcode.json"
plebsUrls = ''
data_servistate = json.load(open(servistate_file))
#data_search     = json.load(open(search_file))

# check if servistate file
try:
    check = data_servistate["servistate"]
    plebsUrls = data_servistate["stores"]
except KeyError:
    sys.exit("error, json not servistate format")

# check if search file
#try:
#    check = data_search["0"]["posts"]
#    meta  = data_search["meta"]["total_found"]
#    if int(meta) >= 1:
#        plebsUrls = check
#    else:
#        sys.exit("search file has no results")
#except KeyError:
#    sys.exit("error, json not search format")


# files = [f for f in os.listdir('.') if re.match(r'[0-9]+.*\.jpg', f)]

# init
threads      = []  # just bunch of ints
threads_info = []
threads_daily= []
news         = []
events       = []
events_daily = []
eras         = []
plebFiles    = []
# some title json
description  = """1. The purpose is to log events as they happen over the coming days. All of the shit going down in the last week is connected, the sealed indictments, the KSA purge and Lebanon tension, Trump donning a bomber jacket in the Pacific. We are here to record and analyze because no one else will be able to do a better job than /us/.<br>
              2. Everyone is aware of the presence of b0ts and derailers in these threads. Focus, Believe, and make a choice right now: Do you Trust Trump?<br>
              3. How would *you* succinctly break all this news to your blue-pilled friend? Does the initial message need to answer every detail? Bring them along for the ride and celebrations lads.<br>
              4. Stick to the graphic and produce infographics for redpilling<br>
              5. Shill are now trying to bake fake breads with dead link. REMEMBER to check for mold in new breads<br>
              6. Get Comfy, Believe in your bones that we're riding the greatest timeline in existence."""
description2  = """Context of news and other events related to Q postings."""
newtitle    = { "text": { "headline": "The Q Chronicles", "text": description },"media": {"url": "img/cbts.jpg","thumb":   "img/cbts.jpg" }}
newstitle   = { "text": { "headline": "News vs. Q", "text": description2 }}
newdata     = { "events": events, "title": newtitle, "eras": eras }
newsdata    = { "events": news, "title": newstitle, "eras": eras }
newdailyindex = {}

# iterate plebs urls and call api if no file(s)
if action == "fetch":
    for plebs in plebsUrls:
        if plebs["name"] == "requests":
            for fetch in plebs["data"]:
                s           = { "url": '', "file": '' }
                s['url']    = fetch["url"]
                s['file']   = "4plebs/" + fetch["name"] + ".json"
                # call api
                process_4plebs_api(s)
                # build timeline data
                plebFiles.append({ "name": fetch["name"], "file": s['file'] })

# fetch via filenames
if action == "convert":
    files = [f for f in os.listdir('4plebs/') if re.match(r'q-anon-[0-9]+.*\.json', f)]
    files_search = [f for f in os.listdir('4plebs/') if re.match(r'searchresult-tripcode-page-[0-9]+.*\.json', f)]
    for fetch in files:
        print "file: " + fetch
        disassembled = urlparse(fetch)
        filename, file_ext = splitext(basename(disassembled.path))
        plebFiles.append({ "name": filename + file_ext, "file": '4plebs/' + fetch })
    for fetch in files_search:
        print "file: " + fetch
        disassembled = urlparse(fetch)
        filename, file_ext = splitext(basename(disassembled.path))
        plebFiles.append({ "name": filename + file_ext, "file": '4plebs/' + fetch })

# iterate plebs and process
for plebs in plebFiles:
    print "processing: ",plebs["name"]
    data = json.load(open(plebs['file']))
    # parse complete timeline
    for npost in data['0']['posts']:
#       print "parsing:",npost['num']
        # process context related posts ()
        # context posts / replies
        try:
            cp = npost["comment_processed"]
        except KeyError:
            pass

        if cp:
            soup = BeautifulSoup(htmlparser.unescape(cp.decode("utf-8")))
            for slink in soup.findAll('a'):
                # is backlink?
                isbl = slink.get('class')
                dtps = slink.get('data-post')
                if isbl == "backlink":
                    # fetch this backlink
                    print "fetching backlink:",dtps
                    process_4plebs_api({ "url": "http://archive.4plebs.org/_/api/chan/post/?board=pol&num=" + dtps, "file": "compiled/json/posts/post_" + dtps + ".json" })
                    # add info as media
                    npost['backlink'] = dtps
                    break

        r = process_4plebs_post(npost,"detail")
        n = process_4plebs_post(npost,"news")

        r['group'] = "QAnon"
        # add to global timeline
        if r not in events:
            events.append(r)

        news.append(n)
        # add to events_daily
        if r not in events_daily:
            events_daily.append(r)

        # add threads
        if npost['thread_num']:
            item = int(npost['thread_num'])
            if item not in threads:
                threads.append(item)

# build index before adding thread infos to events
for npost in events:
    identdate = npost['_identdate']
    newdailyindex[identdate] = {}

# fetch threads
for thread in threads:
    print "processing: thread", thread
    r = process_4plebs_thread(thread)
    # add to global timeline
    events.append(r)
    # build thread info index
    threads_info.append(r)


# reparse result and sort per day
for key,value in newdailyindex.iteritems():
    f = "compiled/json/q_day_"+key+".json"
    n = "data_news/news-"+key+".json"
    nexists = False
    npdata  = ''
    npresult= ''

    # stupid iterate to events again
    events_per_day = []
    newdata_per_day = { "events": events_per_day}

    if os.path.exists(n):
        fexists = True
        npdata  = json.load(open(n))
        for np in npdata['news']:
            npresult = process_news_post(np)
            npresult['group'] = "NEWS"
            news.append(npresult)
            #events_per_day.append(npresult)

    # iterate posts (copied) again
    for npost in events_daily:
        identdate   = npost['_identdate']
        identthread = npost['thread_num']
        if identdate == key:
            events_per_day.append(npost)
            # iterate threads
            for ndata in threads_info:
                thidentnum = ndata['thread_ident']
                if str(thidentnum) == str(identthread):
                    if ndata not in events_per_day:
                        events_per_day.append(ndata)

    if action == "convert":
        # write to daily json
        rd = json.dumps(newdata_per_day)
        fh = open(f, 'w')
        fh.write(rd)
        fh.close()
        print "wrote:",f

if action == "convert":
    # save complete timeline
    f  = "compiled/json/q.json"
    rd = json.dumps(newdata)
    fh = open(f, 'w')
    fh.write(rd)
    fh.close()
    print "wrote:",f

    # save news timeline
    f  = "compiled/json/news.json"
    rd = json.dumps(newsdata)
    fh = open(f, 'w')
    fh.write(rd)
    fh.close()
    print "wrote:",f

# kek
