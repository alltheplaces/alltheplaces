import json
import re
from urllib.parse import unquote

from scrapy.spiders import SitemapSpider

from locations.categories import PaymentMethods, apply_yes_no
from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider

# Five Guys Structured Data


class FiveGuysAESpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_ae"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.ae/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.ae\/en_ae\/[^/]+$", "parse_sd")]
    wanted_types = ["FastFoodRestaurant"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = item["website"] = response.url
        if m := re.search(r"decodeURIComponent\(\"(.+)\"\)", response.text):
            data = json.loads(unquote(m.group(1)))
            item["ref"] = str(data["document"]["id"])
            item["branch"] = data["document"]["geomodifier"]
            item["extras"]["ref:google"] = data["document"].get("googlePlaceId")
            item["lat"] = data["document"]["yextDisplayCoordinate"]["latitude"]
            item["lon"] = data["document"]["yextDisplayCoordinate"]["longitude"]

            payment_methods = data["document"]["c_aboutSectionPaymentMethods"]
            apply_yes_no(PaymentMethods.AMERICAN_EXPRESS, item, "AMERICAN_EXPRESS" in payment_methods)
            apply_yes_no(PaymentMethods.DISCOVER_CARD, item, "DISCOVER" in payment_methods)
            apply_yes_no(PaymentMethods.MAESTRO, item, "MAESTRO" in payment_methods)
            apply_yes_no(PaymentMethods.MASTER_CARD, item, "MASTERCARD" in payment_methods)
            apply_yes_no(PaymentMethods.VISA, item, "VISA" in payment_methods)

        yield item
