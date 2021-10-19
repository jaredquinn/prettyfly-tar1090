import os
import gzip
import json

class RegoCache:

    def __init__(self, progargs):
        self._args = progargs

        self._data = {}
        self._types = {}
        self._loaded = []
        self._ranges = []

        self.OPERATORS = {}
        self.LANG = {}
        self.IDENT = {}


        filePath = os.path.join(self._args.tar_db, 'git-db', 'db', "icao_aircraft_types2.js")
        with gzip.open(filePath, 'rb') as rd:
            types = json.load(rd)
            for t in types.keys():
                self._types[t] = types[t]
            rd.close()

        with open(os.path.join(self._args.data_dir, "country.json"), 'r') as rd:
            ranges = json.load(rd)
            for r in ranges:
                r['start'] = int(r['start'], 16)
                r['end'] = int(r['end'], 16)
                self._ranges.append(r)

            rd.close()

        with open(os.path.join(self._args.data_dir, "ident.json"), 'r') as rd:
            self.IDENT = json.load(rd)

        fp = os.path.join(self._args.data_dir, "ident_local.json")
        if os.path.isfile(fp):
            with open(fp, 'r') as rd:
                moreOps= json.load(rd)
                self.IDENT.update(moreOps)
                rd.close()


        with open(os.path.join(self._args.data_dir, "operators.json"), 'r') as rd:
            self.OPERATORS = json.load(rd)
            rd.close()

        fp = os.path.join(self._args.data_dir, "operators_local.json")
        if os.path.isfile(fp):
            with open(fp, 'r') as rd:
                moreOps= json.load(rd)
                self.OPERATORS.update(moreOps)
                rd.close()

        with open(os.path.join(self._args.data_dir, "lang.json"), 'r') as rd:
            self.LANG = json.load(rd)
            rd.close()

    def get_frame_type(self, type_name):
        DEFAULT = { 'name': 'Unknown', 'emoji': ' ' }
        return self.LANG.get('frametypes').get(type_name, DEFAULT)

    def get_class_data(self, class_name):
        DEFAULT = { 'name': 'unknown', 'emoji': ' ' }
        return self.LANG.get('classes').get(class_name, DEFAULT)

    def get_type_emoji(self, type_name):
        return self.get_frame_type(type_name).get('emoji')

    def get_country_emoji(self, country_name):
        for i in self._ranges:
            if country_name == i.get('country', None):
                return i.get('emoji', ' ')

    def get_country(self, rego):

        if rego is None or rego[0] == '~':
            return None

        rint = int(rego,16)
        for i in self._ranges:
            if rint > i['start'] and rint < i['end']:
                return i
        return None

    def get_type(self, aircraft_type):
        return self._types.get(aircraft_type, None)

    def get_rego(self, regoHex):

        if regoHex not in self._data:
            self.load_rego(regoHex.upper())

        return self._data[regoHex.upper()]


    def load_rego(self, regoHex):

        for c in [3,2,1]:
            prefix = regoHex[0:c]
            filePath = os.path.join(self._args.tar_db, 'git-db', 'db', "%s.js" % prefix)
            if os.path.exists(filePath):

                if not prefix in self._loaded:
                    with gzip.open(filePath, 'rb') as rd:
                        rego_list = json.load(rd)

                        for k in rego_list.keys():
                            self._data['{}{}'.format(prefix, k)]=rego_list[k]

                        rd.close()

                    self._loaded.append(prefix)

        if regoHex not in self._data:
            self._data[regoHex] = None

        return self._data[regoHex]


