import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PoieszSupermarktenNLSpider(SitemapSpider, StructuredDataSpider):
    name = "poiesz_supermarkten_nl"
    item_attributes = {"brand": "Poiesz", "brand_wikidata": "Q2521700"}
    sitemap_urls = ["https://www.poiesz-supermarkten.nl/sitemap.xml"]
    sitemap_rules = [(r"https://www.poiesz-supermarkten.nl/onze-winkels/.*$", "parse_store")]
    wanted_types = ["GroceryStore"]
    search_for_image = False
    search_for_facebook = False

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        # Town pages only show today's hours, so follow their links to the store pages instead.
        if response.xpath('//div[contains(@class, "single-store")]'):
            yield from self.parse_sd(response)
        else:
            for href in response.xpath('//a[starts-with(@href, "onze-winkels/")]/@href').getall():
                yield response.follow(href, callback=self.parse_store)

    def pre_process_data(self, ld_data: dict, **kwargs: Any) -> None:
        ld_data["name"] = ld_data.get("name", "").replace("\xa0", " ")
        if isinstance(ld_data.get("openingHours"), list):
            ld_data["openingHours"] = [rule.replace("\xa0", " ") for rule in ld_data["openingHours"]]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Poiesz Supermarkt,").strip()

        # Poiesz.GoogleMaps.init(53.018216, 5.662921)
        script = response.xpath('//script[contains(text(), "GoogleMaps.init(")]/text()').get("")
        if m := re.search(r"GoogleMaps\.init\((-?\d+\.\d+),\s*(-?\d+\.\d+)\)", script):
            item["lat"], item["lon"] = m.groups()

        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
