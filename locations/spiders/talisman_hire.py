from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.spiders.buco_na_za import BucoNAZASpider
from locations.spiders.builders import BuildersSpider
from locations.structured_data_spider import StructuredDataSpider


class TalismanHireSpider(SitemapSpider, StructuredDataSpider):
    name = "talisman_hire"
    item_attributes = {"brand": "Talisman Hire", "brand_wikidata": "Q120885726"}
    allowed_domains = ["www.talisman.co.za"]
    sitemap_urls = ["https://www.talisman.co.za/googlesitemap"]
    sitemap_rules = [(r"talisman\.co\.za/[-\w]+/[-\w]+/talisman-hire-[-\w]+$", "parse_sd")]
    skip_auto_cc_spider_name = True
    skip_auto_cc_domain = True
    drop_attributes = {"facebook", "twitter"}

    def pre_process_data(self, ld_data: dict, **kwargs):
        ld_data.get("address", {}).pop("addressCountry", None)  # It's always ZA, which isn't true

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Talisman Hire ")
        if item.get("state") == "Mpumalanga":  # country wrongly reverse geocoded as SZ
            item["country"] = "ZA"

        if "inside-" in response.url:
            located_in_location = response.url.split("inside-")[-1].strip("/")
            if located_in_location == "buco":
                item["located_in"] = BucoNAZASpider.item_attributes["brand"]
                item["located_in_wikidata"] = BucoNAZASpider.item_attributes["brand_wikidata"]
            elif located_in_location == "builders":
                item["located_in"] = BuildersSpider.item_attributes["brand"]
                item["located_in_wikidata"] = BuildersSpider.item_attributes["brand_wikidata"]
            elif located_in_location == "builders-express":
                item["located_in"] = located_in_location.replace("-", " ").title()
                item["located_in_wikidata"] = BuildersSpider.item_attributes["brand_wikidata"]
            else:
                item["located_in"] = located_in_location.replace("-", " ").title()
        yield item
