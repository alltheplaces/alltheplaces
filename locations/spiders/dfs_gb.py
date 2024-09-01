import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser


class DfsGBSpider(SitemapSpider):
    name = "dfs_gb"
    item_attributes = {"brand": "DFS", "brand_wikidata": "Q5204927"}
    # There is also https://www.dfs.ie/sitemap.xml, both list all stores!
    sitemap_urls = ["https://www.dfs.co.uk/sitemap.xml"]
    sitemap_rules = [("/store-directory/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        store = DictParser.get_nested_key(data, "store")
        store.update(store["yextDisplayCoordinate"])
        item = DictParser.parse(store)
        item["phone"] = None
        item["ref"] = item["website"] = response.url
        item["branch"] = item.pop("name").removeprefix("DFS ")
        yield item
