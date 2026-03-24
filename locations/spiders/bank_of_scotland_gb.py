import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BankOfScotlandGBSpider(SitemapSpider, StructuredDataSpider):
    name = "bank_of_scotland_gb"
    item_attributes = {
        "brand": "Bank of Scotland",
        "brand_wikidata": "Q627381",
    }
    sitemap_urls = ["https://branches.bankofscotland.co.uk/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/branches\.bankofscotland\.co\.uk\/[-\w]+\/([-\/'\w]+)$",
            "parse_sd",
        )
    ]
    drop_attributes = {"image"}
    time_format = "%H.%M"

    def extract_amenity_features(self, item: Feature, response: Response, ld_item: dict):
        amenities = [s.get("name") for s in (ld_item.get("amenityFeature") or [])]

        apply_yes_no(Extras.WIFI, item, "Wi-Fi" in amenities)
        apply_yes_no(Extras.WHEELCHAIR, item, "Wheelchair access" in amenities)
        apply_yes_no(Extras.CASH_IN, item, "Paying-in machine" in amenities)

        has_atm = any(re.search(r"cashpoint|cash machine", name or "", re.IGNORECASE) for name in amenities)
        apply_yes_no(Extras.ATM, item, has_atm)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.BANK, item)
        yield item
