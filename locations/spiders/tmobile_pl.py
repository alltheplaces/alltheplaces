from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_PL, OpeningHours


class TMobilePLSpider(Spider):
    name = "tmobile_pl"
    item_attributes = {"brand": "T-Mobile International", "brand_wikidata": "Q327634"}
    start_urls = ["https://www.t-mobile.pl/c/_bffapi/sdr-shops/v1/shops"]

    def parse(self, response, **kwargs):
        for feature in response.json():
            item = DictParser.parse(feature)
            item["lat"] = feature["coordinates"]["y"]
            item["lon"] = feature["coordinates"]["x"]
            if len(feature["contact"]["email"]) > 0:
                item["email"] = feature["contact"]["email"]
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(ranges_string=feature["hours"]["txt"], days=DAYS_PL)
            yield item
