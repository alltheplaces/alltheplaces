import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class TjsamgorHKSpider(SitemapSpider):
    name = "tjsamgor_hk"
    item_attributes = {"brand_wikidata": "Q113365214"}
    sitemap_urls = ["https://www.tjsamgor.com/hk/wpsl_stores-sitemap.xml"]
    sitemap_rules = [(r"\?lang=en", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(
            re.search(r'locations":\[(.*)\]', response.xpath('//*[contains(text(),"storeMarker")]/text()').get()).group(
                1
            )
        )
        item = DictParser.parse(raw_data)
        item["branch"] = raw_data["store"]
        item["website"] = response.url
        apply_category(Categories.RESTAURANT, item)
        yield item
