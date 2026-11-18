from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_NL, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class OdidoNLSpider(SitemapSpider, StructuredDataSpider):
    name = "odido_nl"
    item_attributes = {"brand": "Odido", "brand_wikidata": "Q28406140"}
    sitemap_urls = ["https://www.odido.nl/robots.txt"]
    sitemap_rules = [(r"nl/winkels/[^/]+/[^/]+$", "parse")]
    wanted_types = ["Store"]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["image"] = (item.get("image") or "").replace("https://www.odido.nlhttps://", "https://")
        item["branch"] = item.pop("name").removeprefix("Shop ")
        item.pop("state", None)

        # openingHoursSpecification holds plain strings such as "Mo 10:00 - 18:00" or "Su Gesloten"
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            ", ".join(ld_data.get("openingHoursSpecification") or []), closed=CLOSED_NL
        )

        apply_category(Categories.SHOP_TELECOMMUNICATION, item)

        yield item
