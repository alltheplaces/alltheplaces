import json
from typing import Any, AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EndlichOhneDESpider(SitemapSpider, StructuredDataSpider):
    name = "endlich_ohne_de"
    item_attributes = {"brand": "Endlich Ohne", "brand_wikidata": "Q119982663"}
    sitemap_rules = [("/standorte/filiale-", "parse_sd")]
    search_for_facebook = False

    async def start(self) -> AsyncIterator[Any]:
        yield Request("https://www.endlich-ohne.de/standorte/", callback=self.parse_coords)

    def parse_coords(self, response: TextResponse, **kwargs):
        self.coords = {}
        for loc in json.loads(response.xpath("//@data-markers").get()):
            self.coords[str(loc["id"])] = (loc["latLang"]["lat"], loc["latLang"]["lng"])
        yield Request("https://www.endlich-ohne.de/standorte-sitemap.xml", self._parse_sitemap)

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        # Filter out non-location entities
        if not item.get("street_address"):
            return

        if link := response.xpath('//link[@rel="shortlink"]/@href').get():
            ref = link.rsplit("=", 1)[1]
            item["lat"], item["lon"] = self.coords.get(ref, (None, None))

        if "PLZ" in item.get("postcode"):
            item["postcode"] = None

        item["branch"] = item.pop("name", "").removeprefix("ENDLICH OHNE Tattooentfernung ")

        if google_review_link := response.xpath('//a[contains(@href, "placeid=")]/@href').get():
            if place_id := google_review_link.split("placeid=")[1].split("&")[0]:
                item["extras"]["ref:google:place_id"] = place_id

        apply_category(Categories.SHOP_BEAUTY, item)

        yield item
