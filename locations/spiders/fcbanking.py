import json

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FcbankingSpider(SitemapSpider, StructuredDataSpider):
    name = "fcbanking"
    item_attributes = {"brand": "First Commonwealth Bank", "brand_wikidata": "Q5452773"}
    sitemap_urls = ["https://www.fcbanking.com/robots.txt"]
    sitemap_rules = [(r"/branch-locations/[-\w]+/[-\w]+/[-\w]+/[-\w]+", "parse_sd")]
    wanted_types = ["BankOrCreditUnion"]  # Capture only url specific linked data

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        location = json.loads(response.xpath("//@data-location").get(""))
        item["lat"] = location.get("latLng", {}).get("latitude")
        item["lon"] = location.get("latLng", {}).get("longitude")
        item["name"], item["branch"] = item["name"].removesuffix(" Office").split(" - ", 1)
        apply_category(Categories.BANK, item)
        apply_yes_no(
            Extras.ATM,
            item,
            any(
                location.get(atm_key)
                for atm_key in ["hasDriveUpATM", "hasWalkUpATM", "hasOffPremiseWalkUpATM", "hasOffPremiseDriveUpATM"]
            ),
        )
        yield item
