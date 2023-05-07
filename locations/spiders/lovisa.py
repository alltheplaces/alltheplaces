from scrapy import Spider

from locations.dict_parser import DictParser


class LovisaSpider(Spider):
    name = "lovisa"
    item_attributes = {"brand": "Lovisa", "brand_wikidata": "Q106298409"}
    allowed_domains = ["lovisa-stores.herokuapp.com"]
    start_urls = ["https://lovisa-stores.herokuapp.com/all-stores"]

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["ref"] = str(location["branch"])
            item["street_address"] = ", ".join(filter(None, [location.get("address1"), location.get("address2")]))
            item.pop("website")  # websites are generally just malls, not individual stores within
            yield item
