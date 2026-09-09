import json
from typing import Iterable
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SkisetSpider(SitemapSpider, StructuredDataSpider):
    name = "skiset"
    item_attributes = {"brand": "Skiset", "brand_wikidata": "Q48747223"}
    sitemap_urls = ["https://www.skiset.com/sitemap.xml"]
    sitemap_rules = [(r"https://www\.skiset\.com/.*/magasins/.*", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item.get("facebook") == "https://www.facebook.com/skiset.france/":
            item["facebook"] = None
        item["branch"] = item.pop("name").removeprefix("Skiset ")
        
        if (idx := response.text.find("window.appConfig=")) != -1:
            start = idx + len("window.appConfig=")
            try:
                config, _ = json.JSONDecoder().raw_decode(response.text[start:])
                geo = config.get("shop", {}).get("map", {})
                if geo.get("lat") is not None and geo.get("lng") is not None:
                    item["lat"] = geo["lat"]
                    item["lon"] = geo["lng"]
            except (json.JSONDecodeError, AttributeError):
                pass
        
        apply_category(Categories.SHOP_SPORTS, item)
        yield item
