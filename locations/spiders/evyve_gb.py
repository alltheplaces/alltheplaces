from scrapy import Spider

from locations.dict_parser import DictParser


class EvyveGBSpider(Spider):
    name = "evyve_gb"
    item_attributes = {"brand": "evyve", "brand_wikidata": "Q116698197"}
    start_urls = ["https://evyve.co.uk/umbraco/surface/EvyveCharger/GetChargePointData"]

    def parse(self, response, **kwargs):
        for location in response.json()["data"]:
            if not location["publish"]:
                continue  # "coming soon"

            location["street_address"] = location.pop("address")
            yield DictParser.parse(location)
