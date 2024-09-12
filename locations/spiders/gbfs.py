from scrapy.http import JsonRequest
from scrapy.spiders import CSVFeedSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser

# General Bikeshare Feed Specification
# https://gbfs.mobilitydata.org/

# GBFS is a standardized API for operators of bicycles, scooters, moped, and car rental service providers. This
# spider stats at https://github.com/MobilityData/gbfs which offers a centralised catalog of networks or "systems".
# It then processes each system and collects the docks or "stations" from it. Not every system has stations as some
# are dockless.

BRAND_MAPPING = {
    "Bay Wheels": {
        "names": ["Bay Wheels"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q16971391",
    },
    "BiciMAD": {
        "names": ["bicimad", "BiciMAD (unofficial)"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q17402113",
    },
    "Bicing": {
        "names": ["Bicing"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q1833385",
    },
    "Bike Share Toronto": {
        "names": ["Bike Share Toronto"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q17018523",
    },
    "Bird": {
        "names": [
            "Bird Bordeaux",
            "Bird Cascais",
            "Bird Chalonsenchampagne",
            "Bird Draguignan",
            "Bird Larochesuryon",
            "Bird Laval",
            "Bird Millau",
            "Bird Montlucon",
            "Bird Sarreguemines",
            "Bird Vichy",
        ],
        "category": {"amenity": "kick-scooter_rental"},
        "secondary_category": {"amenity": "bicycle_rental"},
        "wikidata": "",
    },
    "Biki": {
        "names": ["BIXI Montr\u00e9al"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q386",
    },
    "Bolt": {
        "names": ["Bolt Technology O\u00dc"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {"amenity": "kick-scooter_rental"},
        "wikidata": "Q20529164",
    },
    "Call a Bike": {
        "names": ["Call a Bike"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q1060525",
    },
    "Capital Bikeshare": {
        "names": ["Capital Bike Share"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q1034635",
    },
    "Citi Bike": {
        "names": ["Citi Bike"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q2974438",
    },
    "Docomo Bike Share": {
        "names": ["docomo bike share service"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q55533296",
    },
    "Donkey Republic": {
        "names": [
            "Donkey Republic Aalborg",
            "Donkey Republic Aarhus",
            "Donkey Republic Amsterdam",
            "Donkey Republic Antwerp",
            "Donkey Republic Ballerup",
            "Donkey Republic Bamberg",
            "Donkey Republic Budapest",
            "Donkey Republic Cheltenham Spa",
            "Donkey Republic Cirencester",
            "Donkey Republic Copenhagen",
            "Donkey Republic Den Haag",
            "Donkey Republic Dordrecht",
            "Donkey Republic Frederikshavn",
            "Donkey Republic Geneva",
            "Donkey Republic Ghent",
            "Donkey Republic Glostrup",
            "Donkey Republic Gorinchem",
            "Donkey Republic Hiller\u00f8d",
            "Donkey Republic Iisalmi",
            "Donkey Republic Imatra",
            "Donkey Republic Kiel",
            "Donkey Republic Kingham",
            "Donkey Republic Klampenborg",
            "Donkey Republic Kotka",
            "Donkey Republic Kouvola",
            "Donkey Republic Kreuzlingen",
            "Donkey Republic Lappeenranta",
            "Donkey Republic Le Locle",
            "Donkey Republic Liechtenstein",
            "Donkey Republic Malm\u00f6",
            "Donkey Republic M\u00e4nts\u00e4l\u00e4",
            "Donkey Republic Mikkeli",
            "Donkey Republic Moreton In Marsh",
            "Donkey Republic Munich",
            "Donkey Republic Neuch\u00e2tel",
            "Donkey Republic Odense",
            "Donkey Republic Oxford",
            "Donkey Republic Porvoo",
            "Donkey Republic Raasepori",
            "Donkey Republic Regensburg",
            "Donkey Republic Reykjavik",
            "Donkey Republic Riihim\u00e4ki",
            "Donkey Republic Rotterdam",
            "Donkey Republic Rotterdam/Den Haag",
            "Donkey Republic Store Heddinge",
            "Donkey Republic The Cotswold Water Park",
            "Donkey Republic Thun",
            "Donkey Republic Turku",
            "Donkey Republic Utrecht",
            "Donkey Republic Valenciennes",
            "Donkey Republic Worthing",
            "Donkey Republic Yverdon-les-Bains",
        ],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q63753939",
    },
    "Dott": {
        "names": ["Dott Stockholm"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {"amenity": "kick-scooter_rental"},
        "wikidata": "Q107463014",
    },
    "Ecobici": {
        "names": ["Ecobici"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q5817067",
    },
    "HELLO CYCLING": {
        "names": ["HELLO CYCLING"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q91231927",
    },
    "Lyft": {
        "names": ["Lyft Scooters Chicago", "Lyft Scooters Denver"],
        "category": {"amenity": "kick-scooter_rental"},
        "secondary_category": {},
        "wikidata": "Q17077936",
    },
    "Metrorower": {
        "names": ["METROROWER"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q123507620",
    },
    "Mevo": {
        "names": ["MEVO"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q60860236",
    },
    "Neuron Mobility": {
        "names": ["Neuron Mobility"],
        "category": {"amenity": "kick-scooter_rental"},
        "secondary_category": {"amenity": "bicycle_rental"},
        "wikidata": "",
    },
    "Nextbike": {
        "names": [
            "nextbike Bene\u0161ov",
            "nextbike Bergamo",
            "nextbike Berlin",
            "nextbike Berounsko",
            "nextbike BIH",
            "nextbike Brno",
            "nextbike Bulgaria",
            "nextbike Burgenland Austria",
            "nextbike \u010cesk\u00e1 T\u0159ebov\u00e1",
            "nextbike Croatia",
            "nextbike Cyprus",
            "nextbike D\u00fcsseldorf",
            "nextbike Dv\u016fr Kr\u00e1lov\u00e9",
            "nextbike Frankfurt",
            "nextbike Fr\u00fddek-M\u00edstek",
            "nextbike Gie\u00dfen",
            "nextbike G\u00fctersloh",
            "nextbike Hav\u00ed\u0159ov",
            "nextbike Hodon\u00edn",
            "nextbike Ho\u0159ice",
            "nextbike Hradec Kr\u00e1lov\u00e9",
            "nextbike Jablonec",
            "nextbike Ji\u010d\u00edn",
            "nextbike Jihlava",
            "nextbike Kassel",
            "nextbike Kiev",
            "nextbike Kladno",
            "nextbike Klagenfurt Austria",
            "nextbike Kl\u00e1\u0161terec nad Oh\u0159\u00ed",
            "nextbike Konya",
            "nextbike Kop\u0159ivnice",
            "nextbike Leipzig",
            "nextbike Le\u00f3n",
            "nextbike Liberec",
            "nextbike Lippstadt",
            "nextbike LV",
            "nextbike Marburg",
            "nextbike Mladoboleslavsko",
            "nextbike Moravsk\u00e1 T\u0159ebov\u00e1",
            "nextbike Most",
            "nextbike Nieder\u00f6sterreich Austria",
            "nextbike Norderstedt",
            "nextbike OlbramoviceVotice",
            "nextbike Olomouc",
            "nextbike Opava",
            "nextbike Ostrava",
            "nextbike Pelh\u0159imov",
            "nextbike P\u00edsek",
            "nextbike Praha",
            "nextbike P\u0159erov",
            "nextbike Romania",
            "nextbike R\u00fcsselsheim am Main",
            "nextbike Rychnovsko",
            "nextbike Stirling",
            "nextbike Switzerland",
            "nextbike T\u0159eb\u00ed\u010d",
            "nextbike Trutnov",
            "nextbike Uhersk\u00e9 Hradi\u0161t\u011b",
            "nextbike Vinnitsa (Ukraine)",
            "nextbike Vrchlab\u00ed",
            "nextbike Wiesbaden",
            "nextbike Zl\u00edn",
        ],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q2351279",
    },
    "Pony": {
        "names": [
            "Pony Angers",
            "Pony Basque Country",
            "Pony Beauvais",
            "Pony Beziers",
            "Pony Bordeaux",
            "Pony Bourges",
            "Pony Brussels",
            "Pony Charleroi",
            "Pony Evry",
            "Pony Herouville",
            "Pony La Roche-sur-Yon",
            "Pony Li\u00e8ge",
            "Pony Limoges",
            "Pony Lorient",
            "Pony Nice",
            "Pony Olivet",
            "Pony Paris",
            "Pony Perpignan",
            "Pony Poitiers",
        ],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {"amenity": "kick-scooter_rental"},
        "wikidata": "",
    },
    "PubliBike": {
        "names": ["PubliBike"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q3555363",
    },
    "Shared Mobility": {"names": ["sharedmobility.ch"], "category": {}, "secondary_category": {}, "wikidata": ""},
    "TIER": {
        "names": ["TIER Basel", "TIER Bern", "TIER Paris", "TIER Stgallen", "TIER Winterthur", "TIER Zurich"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {"amenity": "kick-scooter_rental"},
        "wikidata": "Q63386916",
    },
    "V\u00e9lib' Metropole": {
        "names": ["V\u00e9lib' Metropole"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q1120762",
    },
    "Velospot": {
        "names": ["Velospot"],
        "category": {"amenity": "bicycle_rental"},
        "secondary_category": {},
        "wikidata": "Q56314221",
    },
    "Voi": {
        "names": ["Voi Marseille", "Voi Switzerland"],
        "category": {"amenity": "kick-scooter_rental"},
        "secondary_category": {},
        "wikidata": "Q61650427",
    },
}


class GbfsSpider(CSVFeedSpider):
    name = "gbfs"
    start_urls = ["https://github.com/MobilityData/gbfs/raw/master/systems.csv"]
    download_delay = 2
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_row(self, response, row):
        yield JsonRequest(url=row["Auto-Discovery URL"], cb_kwargs=row, callback=self.parse_gbfs)

    def parse_gbfs(self, response, **kwargs):
        try:
            data = response.json()
        except:
            return

        for feed in DictParser.get_nested_key(data, "feeds") or []:
            if feed["name"] == "station_information":
                yield JsonRequest(url=feed["url"], cb_kwargs=kwargs, callback=self.parse_stations)

    def parse_stations(self, response, **kwargs):
        try:
            data = response.json()
        except:
            return

        for station in DictParser.get_nested_key(data, "stations") or []:
            if station.get("address"):
                station["street_address"] = station.pop("address")
            station["country"] = kwargs["Country Code"]

            item = DictParser.parse(station)

            item["ref"] = item["extras"]["ref:gbfs"] = "{}:{}".format(kwargs["System ID"], station["station_id"])
            item["extras"]["ref:gbfs:{}".format(kwargs["System ID"])] = str(station["station_id"])

            if "capacity" in station:
                item["extras"]["capacity"] = str(station["capacity"])
            # This URL isn't POI specific, but it is Network specific
            item["website"] = kwargs["URL"]

            # TODO: Map all brands/names
            brand_mapped = False
            for brand in BRAND_MAPPING:
                if kwargs["Name"] in BRAND_MAPPING[brand]["names"]:
                    apply_category(BRAND_MAPPING[brand]["category"], item)
                    item["brand"] = brand
                    item["brand_wikidata"] = BRAND_MAPPING[brand]["wikidata"]
                    brand_mapped = True
                    break
            if not brand_mapped:
                item["brand"] = kwargs["Name"]  # Closer to OSM operator or network?
                if "bike" in kwargs["Name"].lower() or "cycle" in kwargs["Name"].lower():
                    apply_category(Categories.BICYCLE_RENTAL, item)
                else:
                    apply_category({"public_transport": "stop_position"}, item)

            if station.get("is_virtual_station"):
                item["extras"]["physically_present"] = "no"

            yield item
