#! /home/veatch/.envs/wras/bin/python2.7

from datetime import datetime, timedelta
from feedgen.feed import FeedGenerator
from glob import glob
import os
import random
from subprocess import call

MP3_DIR = '/www/veatch/wras/'
HEADER = '/home/veatch/wras/header.txt'
SCHEDULE = {
    # day-hour: {duration, show name}
    "*-6":  ("120", "Rotation"),
    "0-20": ("120", "Georgia-Music-Show"),
    "2-20": ("120", "Distance+Lights"),
    "3-22": ("120", "Mighty-Aphrodite"),
    "5-12": ("120", "Deviltown"),
    "5-16": ("120", "QCS"),
    "5-20": ("120", "Soul-Kitchen"),
    "6-14": ("120", "Melodically-Challenged"),
}
# Should be before earliest scheduled recording. Going with 5 for now so I
# don't have to think about DST at all.
UPDATE_HOUR = 5
MP3_URL_PREFIX = 'http://veat.ch/wras/%s'


def update_web_and_podcast():
    now = datetime.now()
    if now.hour != UPDATE_HOUR:
        return
    files = chdir_get_files()
    delete_old_files(now)
    pick_from_yesterday(now)
    make_podcast(files)
    update_web(files)

def chdir_get_files():
    os.chdir(MP3_DIR)
    return sorted(glob('*.mp3'), reverse=True)

def update_web(files):
    with open(HEADER, 'r') as header_file:
        page = header_file.read()
    for f in files:
        page += '<a href="{0}">{1}</a><br/>'.format(MP3_URL_PREFIX % f, f)
    with open('index.html', 'w') as index_html:
        index_html.write(page)


def make_podcast(files):
    feed = init_feed()
    for f in files:
        item = feed.add_entry()
        url = MP3_URL_PREFIX % f
        item.id(url)
        filename_parts = f.split('-')
        title = ' '.join(filename_parts[4:]).split('.')[0]
        item.title(title)
        date = '/'.join(filename_parts[1:4])
        item.description('%s %s' % (title, date))
        item.link(href=url)
        size = '%s' % os.path.getsize(f)
        item.enclosure(url=url, length=size, type='audio/mpeg')
    feed.rss_file('feed/podcast.xml')


def delete_old_files(now):
    two_weeks_ago = now - timedelta(days=14)
    old_mp3s = 'WRAS-%s*' % two_weeks_ago.strftime('%m-%d')
    for f in glob(old_mp3s):
        os.remove(f)


def pick_from_yesterday(now):
    """
    Of files downloaded yesterday, randomly pick one to keep, delete the rest.
    """
    yesterday = now - timedelta(days=1)
    mp3_prefix = 'WRAS-%s*' % yesterday.strftime('%m-%d')
    mp3s = glob(mp3_prefix)
    if len(mp3s) <= 1:
        return
    pick = randomish_pick(mp3s)
    for f in mp3s:
        if f == pick:
            continue
        os.remove(f)


def randomish_pick(files):
    pick = random.choice(mp3s)
    if os.path.getsize(pick) > 100000000:
        return pick
    # if pick had connection issue and is too small, check for bigger files
    for f in files:
        if os.path.getsize(f) > 100000000:
            return f
    return pick


def init_feed():
    fg = FeedGenerator()
    fg.load_extension('podcast')
    fg.id('http://veat.ch/wras/feed/podcast.xml')
    fg.link(href='http://veat.ch/wras')
    desc = 'A daily two hour sample of WRAS. Listen to the official live stream at http://www2.gsu.edu/~www885/'
    fg.description(desc)
    fg.title('WRAS Album 88')
    fg.logo('http://veat.ch/wras/88half.jpg')
    return fg


def scheduled_show(now):
    hour = now.hour
    day = now.weekday()
    scheduled_show = SCHEDULE.get('*-%s' % hour)
    if scheduled_show is None:
        scheduled_show = SCHEDULE.get('%s-%s' % (day, hour))
        if scheduled_show is None:
            return
    return scheduled_show


def record(show_info, now):
    duration = '%smin' % show_info[0]
    show_name = show_info[1]
    call(["icecream", "--stop=%s" % duration, "http://www.publicbroadcasting.net/wras/ppr/wras2.m3u"])
    filename = 'WRAS-%s-%s.mp3' % (now.strftime('%m-%d-%y'), show_name)
    os.rename('WRAS2.mp3', '%s%s' % (MP3_DIR, filename))

def record_scheduled_show():
    now = datetime.now()
    show_info = scheduled_show(now)
    if not show_info:
        return
    record(show_info, now)


if __name__ == '__main__':
    record_scheduled_show()
    update_web_and_podcast()
