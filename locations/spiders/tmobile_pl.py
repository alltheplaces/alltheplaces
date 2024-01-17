from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_PL, OpeningHours


class TMobilePLSpider(Spider):
    name = "tmobile_pl"
    item_attributes = {"brand": "T-Mobile", "brand_wikidata": "Q327634"}
    start_urls = ["https://www.t-mobile.pl/c/_bffapi/sdr-shops/v1/shops"]

    def parse(self, response, **kwargs):
        street_prefix_mapping = {
            "Os.": "Osiedle",
            "Al.": "Aleja",
            "Pl.": "Plac",
            "Ul.": None,  # ulica (street) is omitted - OSM convention in Poland
        }
        for feature in response.json():
            item = DictParser.parse(feature)
            item["lat"] = feature["coordinates"]["y"]
            item["lon"] = feature["coordinates"]["x"]
            if len(feature["contact"]["email"]) > 0:
                item["email"] = feature["contact"]["email"]
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(ranges_string=feature["hours"]["txt"], days=DAYS_PL)
            street_prefix = street_prefix_mapping.get(feature["address"]["street_prefix"], None)
            item["street"] = " ".join(filter(None, [street_prefix, feature["address"]["street"]]))
            yield item
