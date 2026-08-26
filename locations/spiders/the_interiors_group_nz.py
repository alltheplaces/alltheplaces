from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

BRANDS = {
    "carpetcourt.nz": {
        "brand": "Carpet Court",
        "brand_wikidata": "Q137908618",
        "category": Categories.SHOP_CARPET,
        "prefix": "Carpet Court",
    },
    "curtainstudio.co.nz": {
        "brand": "Curtain Studio",
        "brand_wikidata": "Q137908226",
        "category": Categories.SHOP_CURTAIN,
        "prefix": "Curtain Studio",
    },
}


class TheInteriorsGroupNZSpider(SitemapSpider, StructuredDataSpider):
    name = "the_interiors_group_nz"
    allowed_domains = ["carpetcourt.nz", "curtainstudio.co.nz"]
    sitemap_urls = [
        "https://carpetcourt.nz/sitemap_stores.xml",
        "https://curtainstudio.co.nz/sitemap_stores.xml",
    ]
    sitemap_rules = [(r"/our-locations/[^/]+$", "parse_sd")]
    wanted_types = ["HomeGoodsStore"]
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        brand = next(v for k, v in BRANDS.items() if k in response.url)

        item["brand"] = brand["brand"]
        item["brand_wikidata"] = brand["brand_wikidata"]
        apply_category(brand["category"], item)

        item["branch"] = item.pop("name").removeprefix(brand["prefix"]).strip(" -")

        yield item
