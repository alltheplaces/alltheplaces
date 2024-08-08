from scrapy.http import JsonRequest
from scrapy.spiders import CSVFeedSpider

from locations.dict_parser import DictParser

# General Bikeshare Feed Specification
# https://gbfs.mobilitydata.org/

# GBFS is a standardized API for operators of bicycles, scooters, moped, and car rental service providers. This
# spider stats at https://github.com/MobilityData/gbfs which offers a centralised catalog of networks or "systems".
# It then processes each system and collects the docks or "stations" from it. Not every system has stations as some
# are dockless.


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

            item["brand"] = kwargs["Name"]  # Closer to OSM operator or network?
            if "capacity" in station:
                item["extras"]["capacity"] = str(station["capacity"])
            # This URL isn't POI specific, but it is Network specific
            item["website"] = kwargs["URL"]

            # TODO: we could do with the vehicles types, then add OSM tags
            # eg amenity=bicycle_rental, amenity=kick-scooter_rental, amenity=motorcycle_rental, amenity=car_rental
            # but until then, we can do a white lie and call it public transit
            item["extras"]["public_transport"] = "stop_position"

            if station.get("is_virtual_station"):
                item["extras"]["physically_present"] = "no"

            yield item
