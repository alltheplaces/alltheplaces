import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ApiFRSpider(SitemapSpider, StructuredDataSpider):
    name = "api_fr"
    item_attributes = {"brand": "Api", "brand_wikidata": "Q116193091", "name": "Api"}
    sitemap_urls = ["https://superettes.api-masuperette.fr/sitemap.xml"]
    sitemap_rules = [(r"^https://superettes\.api-masuperette\.fr/[^/]+/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["GroceryStore"]
    # Head-office phone, email and Facebook page shared by every store.
    drop_attributes = {"phone", "email", "facebook"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        # Not yet open: the JSON-LD still lists regular hours.
        if response.css(".b-today__status--upcoming"):
            return

        item["ref"] = item["ref"].rsplit("#store-", 1)[-1]
        branch = re.sub(
            r"^Api\s*-?\s*(?:(?:super\s+)?supérette\s+(?:de\s+|d')?)?", "", item.pop("name"), flags=re.IGNORECASE
        )
        # "des Peintures" is "de Les Peintures".
        item["branch"] = re.sub(r"^du\s", "Le ", re.sub(r"^des\s", "Les ", branch))

        # Brand promo photo reused on many stores.
        if item.get("image", "").endswith("/ed707604-bd4f-41f9-9832-70db614945aa.jpg"):
            item.pop("image")

        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
