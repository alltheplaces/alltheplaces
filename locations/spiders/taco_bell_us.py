from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

TACO_BELL_SHARED_ATTRIBUTES = {"brand": "Taco Bell", "brand_wikidata": "Q752941"}
TACOBELL_CANTINA = {"name": "Taco Bell Cantina", "brand": "Taco Bell", "brand_wikidata": "Q111972226"}


class TacoBellUSSpider(SitemapSpider, StructuredDataSpider):
    name = "taco_bell_us"
    item_attributes = TACO_BELL_SHARED_ATTRIBUTES
    sitemap_urls = ["https://locations.tacobell.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/[^/]+\.html$", "parse")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["website"] = response.url

        if "Cantina" in item["name"]:
            item.update(TACOBELL_CANTINA)

        if not item.get("lat"):
            item["lat"] = ld_data.get("latitude")
        if not item.get("lon"):
            item["lon"] = ld_data.get("longitude")

        features = response.xpath('//div[contains(@class, "icons-wrapper")]/div/span/text()').getall()

        apply_yes_no(Extras.DELIVERY, item, "Delivery" in features)
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Thru" in features)

        yield item
