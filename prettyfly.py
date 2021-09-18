#!/usr/bin/env python3

import pprint
import json
import gzip
import shutil
import json
import datetime
import os

from operator import itemgetter
from decimal import Decimal

from lib.cache import RegoCache
from lib.craft import Craft, CraftStat, IncomingCraft

total_messages = 0

import argparse

parser = argparse.ArgumentParser(prog='prettyfly', usage='%(prog)s [options]')
parser.add_argument('--hours', type=int, default=12)
parser.add_argument('--data-dir', nargs='?', default='data')
parser.add_argument('--tar-rundir', nargs='?', default='/run/tar1090')
parser.add_argument('--tar-db', nargs='?', default='/usr/local/share/tar1090')

parser.add_argument('--lon', type=float, default=os.environ.get('LONGITUDE', None))
parser.add_argument('--lat', type=float, default=os.environ.get('LATITUDE', None))

args = parser.parse_args()

#CONFIG = {
#        'LAT': Decimal(-33.88791635484722),
#        'LON': Decimal(151.19752943364472),
#        'RUN': '/run/tar1090',
#        'GITDB': '/usr/local/share/tar1090/git-db',
#        'DB': '/usr/local/share/tar1090/git-db/db',
#}

# Maintained for backwards compatibility
#WORDS = {
#        'jet': [ '🛫 Jet', 'Jet' ],
#        'raaf': [ '✈️  RAAF', 'RAAF' ],
#        'twin': [ '🛩  Twin Prop', 'Twin Prop' ],
#        'prop': [ '🛩  Plane', 'Plane' ],
#        'heli': [ '🚁 Heli', 'Heli' ],
#        'tower': [ '🗼 Tower', 'Tower' ],
#        'rescue': [ '⛑  Rescue', 'Rescue' ],
#        'military': [ '🪖 Army/Navy', 'Army/Navy' ],
#        'medical': [ '🚑 Medical', 'Medical' ],
#        'police': [ '🚔 Police', 'Police' ],
#        'cargo': [ '🎁 Cargo', 'Cargo' ],
#        'tv': [ '🎥 TV/Media', 'TV/Media' ],
#        'raytheon': [ '💣 Raytheon', 'Raytheon' ],
#        'special': [ '🏆 Special', 'Special' ],
#	'fire': [ '🔥 Fire', 'Fire'] 
#}

cache = RegoCache(args)
stats = CraftStat(args, cache)

doAll=False
endTime = datetime.datetime.now()
startTime = datetime.datetime.now()-datetime.timedelta(hours=args.hours)

with open(os.path.join(args.tar_rundir, 'chunks.json'), 'r') as f:
      data = json.load(f)

      for item in data.get('chunks_all', []):
          with gzip.open(os.path.join(args.tar_rundir, item), 'rb') as f_in:
              chunk = json.load(f_in)
              parts = chunk.get('files', [])
              for part in parts:
                  now = datetime.datetime.fromtimestamp(part.get('now'))
                  if doAll==True or (now > startTime and now < endTime):
                      for craft in part.get('aircraft',[]):
                          objCraft = IncomingCraft(craft, cache)
                          #CONFIG)
                          stats.process(objCraft, now, cache)


                      stats.setStartEndTime(now)



dtRange = stats.getTimeFrame()
dtFmt = '%d %b %Y, %H:%M:%S %z'

print('ADS-B Statistics')
print('')
print('From : %s' % dtRange[0].strftime(dtFmt))
print('Until: %s' % dtRange[1].strftime(dtFmt))
print('')
print('Detected {} craft:'.format(stats.count))
print('')
print('By Country of Registration')
print('')

for i in stats.getCountryCountAnnotated():
    emoji = cache.get_country_emoji(i[1])
    print('%2d. %s %s (%d)' % (i[0], emoji, i[1], i[2]))

print('')
print('By Type')
print('')

getFrames = stats.getFrameCounts(cache)

for i in getFrames.get('TYPE'):
    print('%2d. %s (%d)' % (i[0], i[1], i[2]))

print('')
print('Top Airframes:')
print('')
for i in getFrames.get('AIRFRAME'):
    print('%2d. %s (%d %s)' % (i[0], i[1], i[2], i[3]))

print('')
print('Busy Craft (Multiple Callsigns)')
print('')
for i in stats.getMultiCallsign(cache):
    print('%2d. %s (%d: %s)' % (i[0], i[1], i[2], i[3]))

print('')
print('Flights of Interest')
print('')
data = stats.getInterestingCallsigns().items()
for k,v in data:
    if k is not None:
        print('%s %d: %s' % ( k, len(v), ', '.join([ '%s/%s' % (i[1],i[0]) for i in v ]) ) )

print('')

print('Flights by Carrier')
print('')

data = stats.getCarrierCount()
for k in sorted(data, key=lambda k: len(data[k]), reverse=True):

    if len(data[k]) > 0:
        op = cache.OPERATORS.get('callsigns').get(k)
        ln = cache.OPERATORS.get('classes').get(op.get('class'), {})
        em = ln.get('emoji', '🛫')
        lab = k
        info = 'callsigns'
        if lab[0] in ['*', '?']:
            info = 'regos'
            lab = ''

        print('%1s %3d %4s (%s) %s: %s' % ( em, len(data[k]), lab, op.get('name'),info,', '.join(sorted([i[0].replace(k,'') for i in data[k]])) ) )


