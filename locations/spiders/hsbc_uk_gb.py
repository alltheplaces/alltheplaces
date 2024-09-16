from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class HsbcUkGBSpider(SitemapSpider, StructuredDataSpider):
    name = "hsbc_uk_gb"
    item_attributes = {"brand": "HSBC UK", "brand_wikidata": "Q64767453"}
    start_urls = ["https://www.hsbc.co.uk/branch-list/"]
    sitemap_urls = ["https://www.hsbc.co.uk/sitemaps-pages.xml"]
    sitemap_rules = [(r"/branch-list/(.+)/$", "parse_sd")]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if not ld_obj.get("@type"):
                yield ld_obj

    def post_process_item(self, item, response, ld_data):
        item.pop("image", None)
        item.pop("facebook", None)
        item.pop("twitter", None)

        item["website"] = response.url

        services = [
            feature["itemOffered"]["name"] for feature in ld_data.get("hasOfferCatalog", {}).get("itemListElement", [])
        ]
        apply_yes_no(Extras.ATM, item, any("ATM" in s.upper().split() for s in services))
        apply_yes_no(Extras.WIFI, item, "Wi-Fi" in services)
        apply_yes_no(Extras.WHEELCHAIR, item, "Accessible Branch" in services)

        apply_category(Categories.BANK, item)

        yield item
