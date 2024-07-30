from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class NationwideGBSpider(CrawlSpider, StructuredDataSpider):
    name = "nationwide_gb"
    item_attributes = {
        "brand": "Nationwide",
        "brand_wikidata": "Q846735",
        "extras": Categories.BANK.value,
    }
    start_urls = ["https://www.nationwide.co.uk/branches/index.html"]
    rules = [Rule(LinkExtractor(allow=r"/branches/"), callback="parse_sd", follow=True)]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "permanently closed" in item["name"].lower():
            return

        if item["street_address"] is not None and "store is opening" in item["street_address"]:
            # 'addr:street_address': 'This store is opening September/October 2024'
            return

        if "phone" in item and item["phone"] is not None and item["phone"].replace(" ", "").startswith("+443"):
            item.pop("phone", None)

        if (
            "image" in item
            and item["image"] is not None
            and "https://www.bhf.org.uk/-/media/images/social/facebook-share-image_v5-1.png" in item["image"]
        ):
            item.pop("image", None)

        yield item
