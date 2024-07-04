from urllib.parse import urljoin

from scrapy import Spider

from locations.dict_parser import DictParser


class LeroyMerlinPLSpider(Spider):
    name = "leroy_merlin_pl"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    item_attributes = {"brand": "Leroy Merlin", "brand_wikidata": "Q889624"}
    start_urls = ["https://www.leroymerlin.pl/microservices/proxy-api-service/v1/store"]

    def parse(self, response):
        for poi in response.json():
            address = poi.pop("address")
            address["street-address"] = address.pop("street")
            address.pop("id")
            poi.update(address)
            item = DictParser.parse(poi)
            item["phone"] = poi["informationPointPhone"]
            item["website"] = urljoin("https://www.leroymerlin.pl", poi.get("wwwUrl"))
            # TODO: figure out opening hours
            if item["lat"] < 48.99 or item["lat"] > 54.87 or item["lon"] < 14.07 or item["lon"] > 24.13:
                # clearly outside Poland, some locations were claimed to be in the Middle East
                if item["lon"] > 48.99 and item["lon"] < 54.87 and item["lat"] > 14.07 and item["lat"] < 24.13:
                    # swapped lat, lon - swap them back
                    item["lat"], item["lon"] = item["lon"], item["lat"]
                else:
                    del item["lat"]
                    del item["lon"]
            yield item
