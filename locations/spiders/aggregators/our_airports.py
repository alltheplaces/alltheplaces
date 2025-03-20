from scrapy.http import Response
from scrapy.spiders import CSVFeedSpider

from locations.categories import apply_category
from locations.items import Feature, set_closed

CATEGORIES = {
    "balloonport": None,
    "heliport": {"aeroway": "heliport"},
    "large_airport": {"aeroway": "aerodrome", "aerodrome:type": "international"},
    "medium_airport": {"aeroway": "aerodrome"},
    "seaplane_base": {"aeroway": "aerodrome", "aerodrome:type": "seaplane"},
    "small_airport": {"aeroway": "aerodrome"},
}


class OurAirportsSpider(CSVFeedSpider):
    name = "our_airports"
    dataset_attributes = {"license": "Public Domain", "license:wikidata": "Q19652"}
    start_urls = ["https://davidmegginson.github.io/ourairports-data/airports.csv"]

    def parse_row(self, response: Response, row: dict):
        item = Feature()
        item["ref"] = row["id"]
        # item["extras"]["faa"] = row["ident"]  # gps_code #local_code
        item["name"] = row["name"]
        item["lat"] = row["latitude_deg"]
        item["lon"] = row["longitude_deg"]
        item["extras"]["ele:ft"] = row["elevation_ft"]
        item["country"] = row["iso_country"]
        item["extras"]["iata"] = row["iata_code"]
        item["website"] = row["home_link"]
        # item["extras"]["wikipedia"] = row["wikipedia_link"]

        if row["type"] == "closed":
            set_closed(item)
        elif cat := CATEGORIES.get(row["type"]):
            apply_category(cat, item)
        else:
            return None

        yield item
