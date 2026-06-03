from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EndlichOhneDESpider(SitemapSpider, StructuredDataSpider):
    name = "endlich_ohne_de"
    item_attributes = {"brand_wikidata": "Q119982663", "brand": "Endlich Ohne"}
    sitemap_urls = ["https://www.endlich-ohne.de/standorte-sitemap.xml"]
    sitemap_rules = [("/standorte/filiale-", "parse_sd")]
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        # Filter out non-location entities
        if not item.get("street_address"):
            return

        if "PLZ" in item.get("postcode"):
            item["postcode"] = None

        item["branch"] = item.pop("name", "").removeprefix("ENDLICH OHNE Tattooentfernung ")

        if google_review_link := response.xpath('//a[contains(@href, "placeid=")]/@href').get():
            if place_id := google_review_link.split("placeid=")[1].split("&")[0]:
                item["extras"]["ref:google:place_id"] = place_id

        apply_category(Categories.SHOP_BEAUTY, item)

        yield item
