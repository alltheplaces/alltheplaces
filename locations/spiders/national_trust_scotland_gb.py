import json

from scrapy import Spider

from locations.categories import apply_category
from locations.dict_parser import DictParser


class NationalTrustScotlandGBSpider(Spider):
    name = "national_trust_scotland_gb"
    item_attributes = {"operator": "National Trust for Scotland", "operator_wikidata": "Q599997", "nsi_id": "N/A"}
    allowed_domains = ["www.nts.org.uk"]
    start_urls = ["https://www.nts.org.uk/visit/places/search"]

    def parse(self, response):
        jsondata = json.loads(response.xpath('//script[@id="places-result-data"]/text()').get())
        for location in jsondata:
            item = DictParser.parse(location)
            item["lat"], item["lon"] = location["_geoloc"]["lat"], location["_geoloc"]["lng"]
            apply_category({"tourism": "attraction"}, item)
            yield item
