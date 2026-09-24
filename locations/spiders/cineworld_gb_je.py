from typing import Any, Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CineworldGBJESpider(SitemapSpider, StructuredDataSpider):
    name = "cineworld_gb_je"
    item_attributes = {"brand": "Cineworld", "brand_wikidata": "Q5120901"}
    sitemap_urls = ["https://www.cineworld.co.uk/sitemap-0.xml"]
    sitemap_rules = [(r"^https://www\.cineworld\.co\.uk/cinemas/([a-z0-9]+)-.+/$", "parse_sd")]
    wanted_types = ["MovieTheater"]
    search_for_amenity_features = False
    drop_attributes = {"twitter"}
    requires_proxy = "GB"

    def post_process_item(
        self, item: Feature, response: TextResponse, ld_data: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        item["website"] = response.url
        if (item.get("postcode") or "").startswith("JE"):
            item["country"] = "JE"
        apply_category(Categories.CINEMA, item)
        yield item
