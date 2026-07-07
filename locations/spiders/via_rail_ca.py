from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ViaRailCASpider(SitemapSpider, StructuredDataSpider):
    name = "via_rail_ca"
    item_attributes = {"brand": "VIA Rail", "brand_wikidata": "Q876720"}
    sitemap_urls = ["https://www.viarail.ca/sitemap.xml"]
    sitemap_rules = [("/en/explore-our-destinations/stations/", "parse_sd")]
    wanted_types = ["TrainStation"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["name"] = response.xpath("//title/text()").get().replace(" | VIA Rail", "")
        extract_google_position(item, response)
        apply_category(Categories.TRAIN_STATION, item)
        yield item
