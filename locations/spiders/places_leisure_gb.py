from typing import Iterable

from scrapy.http import Response, TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class PlacesLeisureGBSpider(SitemapSpider, StructuredDataSpider):
    name = "places_leisure_gb"
    item_attributes = {"brand": "Places Leisure", "brand_wikidata": "Q130223830"}
    sitemap_urls = ["https://www.placesleisure.org/robots.txt"]
    sitemap_rules = [(r"/centres/[^/]+/$", "parse")]
    wanted_types = ["SportsActivityLocation"]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if not ld_obj.get("@type") and ld_obj.get("type"):
                ld_obj["@type"] = ld_obj.get("type")

            if not ld_obj.get("@type"):
                continue

            types = ld_obj["@type"]

            if not isinstance(types, list):
                types = [types]

            types = [LinkedDataParser.clean_type(t) for t in types]

            for wanted_types in self.wanted_types:
                if isinstance(wanted_types, list):
                    if all(wanted in types for wanted in wanted_types):
                        yield ld_obj
                elif wanted_types in types:
                    yield ld_obj

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["addr_full"] = item.pop("street_address")

        if item.get("email") and item["email"].startswith("mailto@"):
            item["email"] = item["email"].removeprefix("mailto@")

        apply_category(Categories.LEISURE_SPORTS_CENTRE, item)

        yield item
