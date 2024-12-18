from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.spiders.taco_bell_us import TACO_BELL_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class TacoBellCASpider(SitemapSpider, StructuredDataSpider):
    name = "taco_bell_ca"
    item_attributes = TACO_BELL_SHARED_ATTRIBUTES
    sitemap_urls = ["https://locations.tacobell.ca/sitemap.xml"]
    sitemap_rules = [(r"ca/en/\w\w/[^/]+/[^/]+$", "parse")]
    drop_attributes = {"image", "name"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["extras"]["website:en"] = response.url
        item["extras"]["website:fr"] = response.urljoin(
            response.xpath('//a[@data-ya-track="language_fr_CA"]/@href').get()
        )
        yield item

    def extract_amenity_features(self, item, response: Response, ld_item):
        for feature in ld_item.get("amenityFeature") or []:
            if feature["name"] == "Delivery" and feature["value"] == "True":
                apply_yes_no(Extras.DELIVERY, item, True)
            elif feature["name"] == "Drive Thru" and feature["value"] == "True":
                apply_yes_no(Extras.DRIVE_THROUGH, item, True)
