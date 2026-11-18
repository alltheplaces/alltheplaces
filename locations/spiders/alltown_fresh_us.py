import json
import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class AlltownFreshUSSpider(SitemapSpider):
    name = "alltown_fresh_us"
    item_attributes = {"brand": "Alltown Fresh", "brand_wikidata": "Q119591365"}
    sitemap_urls = ["https://alltownfresh.com/sitemap.xml"]
    sitemap_rules = [("/locations/", "parse")]

    def parse(self, response: Response) -> Iterable[Feature]:
        data = json.loads(
            re.search(r"locations\":\[(.+)\]", response.xpath('//*[@id="wpsl-js-extra"]/text()').get()).group(1)
        )
        item = DictParser.parse(data)
        item["street_address"] = item.pop("addr_full")
        item["branch"] = data.get("store").removeprefix("Alltown Fresh ")
        item["website"] = response.url
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
