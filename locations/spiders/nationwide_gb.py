from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class NationwideGBSpider(CrawlSpider, StructuredDataSpider):
    name = "nationwide_gb"
    item_attributes = {
        "brand": "Nationwide",
        "brand_wikidata": "Q846735",
    }
    start_urls = ["https://www.nationwide.co.uk/branches/index.html"]
    rules = [Rule(LinkExtractor(allow=r"/branches/"), callback="parse_sd", follow=True)]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "permanently closed" in item["name"].lower():
            return

        if item["street_address"] is not None and "store is opening" in item["street_address"]:
            # 'addr:street_address': 'This store is opening September/October 2024'
            return

        if "phone" in item and item["phone"] is not None and item["phone"].replace(" ", "").startswith("+443"):
            item.pop("phone", None)

        item["branch"] = item.pop("name").removeprefix("Nationwide ")

        apply_category(Categories.BANK, item)

        yield item

    def extract_amenity_features(self, item, response: Response, ld_item):
        apply_yes_no(Extras.ATM, item, "Cash machine" in ld_item["amenityFeature"]["name"])
