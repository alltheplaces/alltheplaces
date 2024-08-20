from scrapy import Spider

from locations.linked_data_parser import LinkedDataParser


class SamsChickenGBSpider(Spider):
    name = "sams_chicken_gb"
    item_attributes = {"brand": "Sam's Chicken", "brand_wikidata": "Q24439129"}
    start_urls = ["https://www.samschicken.co.uk/index"]
    no_refs = True

    def parse(self, response, **kwargs):
        for ld in LinkedDataParser.iter_linked_data(response):
            item = LinkedDataParser.parse_ld(ld)

            item["image"] = item["name"] = item["state"] = None

            yield item
