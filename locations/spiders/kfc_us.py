from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
from locations.items import set_closed
from locations.structured_data_spider import StructuredDataSpider

KFC_SHARED_ATTRIBUTES = {"brand": "KFC", "brand_wikidata": "Q524757"}


class KfcUSSpider(SitemapSpider, StructuredDataSpider):
    name = "kfc_us"
    item_attributes = KFC_SHARED_ATTRIBUTES
    sitemap_urls = ["https://locations.kfc.com/sitemap.xml"]
    sitemap_rules = [(r"com/\w\w/[^/]+/[^/]+$", "parse")]
    download_delay = 0.5
    wanted_types = ["FoodEstablishment"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = item["image"] = None
        if all(rule.endswith(" Closed") for rule in ld_data.get("openingHours", [])):
            set_closed(item)

        services = response.xpath('//*[contains(@class, "CoreServices-label")]/text()').getall()

        # apply_yes_no(, item, "Catering" in services)
        apply_yes_no(Extras.DELIVERY, item, "Delivery" in services)
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru" in services)
        # apply_yes_no(, item, "Gift Cards" in services)
        apply_yes_no(Extras.WIFI, item, "WiFi" in services)

        yield item
