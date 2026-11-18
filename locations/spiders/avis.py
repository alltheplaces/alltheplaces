from typing import Iterable

from scrapy import Request
from scrapy.http import Response, TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature, set_closed
from locations.structured_data_spider import StructuredDataSpider


class AvisSpider(SitemapSpider, StructuredDataSpider):
    name = "avis"
    item_attributes = {"brand": "Avis", "brand_wikidata": "Q791136"}
    sitemap_urls = ["https://www.avis.com/sitemap.xml"]
    sitemap_rules = [(r"https://www.avis.com/en/locations/[^/]+/[^/]+/[^/]+/[^/]+(?:/[^/]+)?$", "parse_sd")]
    wanted_types = ["AutoRental"]
    drop_attributes = {"image", "twitter"}

    def _parse_sitemap(self, response: Response) -> Iterable[Request]:
        for request in super()._parse_sitemap(response):
            # Pages that return 5xx to Scrapy but work in a browser (likely bot detection)
            request.meta["handle_httpstatus_list"] = [500, 502, 503]
            # response already has data, so don't retry
            request.meta["dont_retry"] = True
            yield request

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        # Collect locationId as ref
        item["ref"] = response.url.strip("/").split("#")[0].rsplit("/", 1)[-1]
        item.pop("name", None)
        item["branch"] = response.xpath('//*[@data-testid="location-list-view-item-heading"]/text()').get("").title()
        if "Closed " in item["branch"].title():
            item["branch"] = None
            set_closed(item)

        apply_category(Categories.CAR_RENTAL, item)

        yield item
