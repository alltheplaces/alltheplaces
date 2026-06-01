import json
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BestoneGBSpider(SitemapSpider, StructuredDataSpider):
    name = "bestone_gb"
    item_attributes = {"brand": "Best-one", "brand_wikidata": "Q4896532"}
    sitemap_urls = ["https://stores.best-one.co.uk/sitemap.xml"]
    drop_attributes = {"name", "image", "facebook"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        for block in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            try:
                data = json.loads(block)
            except json.JSONDecodeError:
                continue
            geo = data.get("credentialSubject", {}).get("geo") if isinstance(data, dict) else None
            if isinstance(geo, dict) and geo.get("latitude") and geo.get("longitude"):
                item["lat"] = geo["latitude"]
                item["lon"] = geo["longitude"]
                break

        yield item
