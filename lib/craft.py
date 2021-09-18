
import json
from .utils import haversine

from decimal import Decimal

class Craft:

    def __set_if_smaller(self, attribute, value, NoneList=[None,'None']):
        if self._data.get(attribute, 'None') in NoneList:
            self._data[attribute] = value
        if value < self._data[attribute]:
            self._data[attribute] = value

    def __set_if_larger(self, attribute, value, NoneList=[None,'None']):
        if self._data.get(attribute, 'None') in NoneList:
            self._data[attribute] = value
        if value > self._data[attribute]:
            self._data[attribute] = value

    @property
    def id(self):
        return self._data.get('id')

    @property
    def rego(self):
        return self._data.get('rego')

    @property
    def airframe(self):
        return self._data.get('airframe')

    @property
    def callsigns(self):
        return self._data.get('callsigns', [])

    @property
    def country(self):
        return self._data.get('country')

    def set_country(self, country):
        self._data['country'] = country

    def set_airframe(self, airframe):
        #print(airframe)
        if airframe is not None:
            self._data['rego'] = airframe[0]
            self._data['airframe'] = airframe[1]
            self._data['what'] = airframe[2]
            self._data['description'] = airframe[3]

    def set_frametype(self, frametype):
        if frametype is not None:
            #print(frametype)
            self._data['wtc'] = frametype[2]
            self._data['frame_type'] = frametype[1]
            self._data['body_desc'] = frametype[0]


    def __init__(self, incoming, now):
        self._data = { 'id': None, 'callsigns': [], 'rego': None }

        if self._data['id'] is None:
            self._data['id'] = incoming.id

        self.update(incoming, now)


    def update(self, incoming, now=None):

        if incoming.callsign is not None:
            if incoming.callsign not in self._data['callsigns']:
                self._data['callsigns'].append(incoming.callsign)

        if incoming.altitude is not None:
            self.__set_if_smaller('altLowest', incoming.altitude)
            self.__set_if_larger('altHighest', incoming.altitude)

        if incoming.distance is not None:
            self.__set_if_smaller('distClosest', incoming.distance)
            self.__set_if_larger('distFurther', incoming.distance)

        if now is not None:
            self.__set_if_smaller('firstSeen', now)
            self.__set_if_larger('lastSeen', now)



class IncomingCraft:

    @property
    def id(self):
        return self._data['id']

    @property
    def altitude(self):
        return self._data['altitude']

    @property
    def distance(self):
        return self._data.get('distance', None)

    @property
    def callsign(self):
        return self._data.get('callsign', None)

    def __str(self):
        return str(self._data)


    def __init__(self, payload, cache):

        self._cache = cache

        self._data = {
                'id': None,
                'altitude': None,
        }

        self._data['id'] = payload[0]

        if payload[1] not in ('None', 'ground'):
            self._data['altitude'] = payload[1]
            self._data['messages'] = payload[9]

            if payload[8] is not None:
                self._data['callsign'] = payload[8].replace(' ', '')


            if payload[4] is not None:
                self._data['lon'] = Decimal(payload[4])
                self._data['lat'] = Decimal(payload[5])


            if self._cache._args.lat is not None and self._cache._args.lon is not None:
                self._data['distance'] = haversine(self._data['lon'], self._data['lat'], self._cache._args.lat, self._cache._args.lon)




class CraftStat:

    def __init__(self, args, cache):
        print(args)

        self._args = args
        self._cache = cache

        self.data = {}

        self.BODY_DESC = {}
        self.STATS = {}
        self.CRAFTS = {}
        self.count = 0


    def getCountryCount(self):
        RESULTS = {}

        for i,v in self.CRAFTS.items():
            if v.country is not None:
                country = v.country.get('country')
                if country not in RESULTS:
                    RESULTS[country] = 0
                RESULTS[country] = RESULTS[country] + 1

        return sorted([(value,key) for (key,value) in RESULTS.items()], reverse=True)

    def getCountryCountAnnotated(self):
        last = 99999999
        pos = 0
        for v,k in self.getCountryCount():
            if v < last:
                last = v
                pos = pos + 1
            yield([pos, k, v])

    def getCarrierCount(self):
        RESULTS = { '???': [], '***': [] }
        PREFIXES = {}

        for i,v in self.CRAFTS.items():

            for c in v.callsigns:
                prefix = ''.join([a for a in c[0:4] if a in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'])
                csObj = self._cache.OPERATORS.get(prefix, None)

                if csObj:
                    operator = self._cache.OPERATORS.get(prefix)
                    if prefix not in RESULTS:
                        RESULTS[prefix] = []
                    RESULTS[prefix].append([c,v.rego])
                else:
                    if prefix in v.rego or v.rego.replace('-','') == c:
                        key = '***'

                        reg = self._cache.IDENT.get('registrations').get(v.rego)
                        if reg is not None:
                            al = reg.get('airline', None)
                            if al is not None:
                                key = al

                        if key not in RESULTS:
                            RESULTS[key] = []
                        if c not in RESULTS[key]:
                            RESULTS[key].append([v.rego,c])
                    else:
                        if c not in RESULTS['???']:
                            RESULTS['???'].append(['%s/%s' % (c,v.rego), c])
                        PREFIXES[prefix] = True



        return RESULTS
        

    def getInterestingCallsigns(self):

        RESULTS = {}
        CALL = []

        def addResult(callsign, rego, cls):
            key = '%s/%s' % (callsign, rego)
            #print('adding [%s] %s %s to %s' % (key, callsign, rego, cls))

            if key not in CALL:
                CALL.append(key)
                #print(CALL)

                if cls not in RESULTS:
                    RESULTS[cls] = []
                RESULTS[cls].append([callsign,rego])


        for i,v in self.CRAFTS.items():

            rgObj = self._cache.IDENT.get('registrations').get(v.rego, None)
#            print(v.rego, rgObj)
            if rgObj is not None:
                for c in v.callsigns:
                    addResult(c, v.rego, rgObj.get('class'))

            else:
                for c in v.callsigns:
                    prefix = ''.join([a for a in c if a in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'])
                    csObj = self._cache.OPERATORS.get(prefix, None)

                    if csObj is not None:
                        cls = csObj.get('class')
                        if cls is not None:
                            addResult(c, v.rego, cls)

            me = int(v.id, 16)
            for m in self._cache.IDENT.get('military'):
                start = int('0x%s' % m[0],16)
                end = int('0x%s' % m[1],16)
                if me > start and me < end:
                    for c in v.callsigns:
                        addResult(c, v.rego, 'military')


        return RESULTS

    def getFrameCounts(self, cache):
        FRAMES={}
        for k,i in self.CRAFTS.items():
            if i.airframe is not None:
                if i.airframe not in FRAMES:
                    FRAMES[i.airframe] = 0
                FRAMES[i.airframe] = FRAMES[i.airframe] + 1


        position = 0
        lastv = 9999

        CLASSES = {}
        RESULTS = []
        SUMMARY = []

        for s,v in sorted([(value,key) for (key,value) in FRAMES.items()], reverse=True): #[0:5]:
            body = self.BODY_DESC.get(v, None)
            if body:
                if body['frame'][1] == 'TWR':
                    CLASSES['TWR'] = CLASSES.get('TWR',0) + s
                else:
                    bodyT = body['body'][2]

                    if body['body'][1][0] == 'H':
                        bodyT = 'HELI'

                    if body['body'][1][0] == 'L':
                        if body['body'][1][2] == 'J':
                            bodyT = 'JET'
                        else:
                            bodyT = 'PROP'
                            if body['body'][1][1] == '2':
                                bodyT = 'TWINPROP'

                    if body['body'][1][0] == 'A':
                        bodyT = 'AMPHIB'

                    if s < lastv:
                        position = position + 1
                        lastv = s

                    pl = ''
                    if s > 1:
                        pl = 's'


                    CLASSES[bodyT] = CLASSES.get(bodyT,0) + s

                    RESULTS.append([position, body['body'][0], s, '{}{}'.format(bodyT, pl)])

        pl = ''
        if CLASSES.get('Tower',0) > 1:
            pl = 's'
        RESULTS.append([position+1, "ADS-B Ground Station", CLASSES.get('TWR'), '{}{}'.format('TWR', pl)])

        lastv = 9999999
        position = 0

        for s,v in sorted([(value,key) for (key,value) in CLASSES.items()], reverse=True):
            if s < lastv:
                position = position + 1
                lastv = s
            SUMMARY.append([position, v, s])

        return { 'AIRFRAME': RESULTS, 'TYPE': SUMMARY }

    def getMultiCallsign(self, cache):

        RESULTS = []
        lastv = 9999999
        position = 0
        for i,v in sorted([(len(value.callsigns),key) for (key,value) in self.CRAFTS.items() if len(value.callsigns) > 2], reverse=True):
            craft = self.CRAFTS.get(v)
            if craft.airframe != 'TWR':
                if i < lastv:
                    position = position + 1
                    lastv = i 
                RESULTS.append([position, craft.rego, i, ', '.join(craft.callsigns)])
        return RESULTS


    def getStats(self):
        return self.STATS

    def getCraft(self):
        #for k,v in self.CRAFTS.items():
        #    print('%s=%s'%(k,v._data))
        return

    def count(self):
        return self.count

    def getTimeFrame(self):
        return (self.data.get('First', None), self.data.get('Last', None))

    def setStartEndTime(self, now):
        if self.data.get('First', None) is None:
            self.data['First'] = now
        self.data['Last'] = now

    def process(self, incoming, now, cache=None):

        if incoming.id not in self.CRAFTS.keys():

            self.count = self.count + 1
            craft = Craft(incoming, now)

            if cache is not None:

                craft.set_country(cache.get_country(incoming.id))

                airframe = cache.get_rego(incoming.id)
                craft.set_airframe(airframe)

                if airframe is not None:
                    self.BODY_DESC[airframe[1]] = { 'frame': airframe, 'body': None }

                body = cache.get_type(craft.airframe)
                craft.set_frametype(body)
                if body is not None:
                    self.BODY_DESC[airframe[1]]['body'] = body

            self.CRAFTS[incoming.id] = craft
        else:
            self.CRAFTS[incoming.id].update(incoming)

