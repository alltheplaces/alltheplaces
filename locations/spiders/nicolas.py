import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.structured_data_spider import extract_phone


class NicolasSpider(SitemapSpider):
    name = "nicolas"
    item_attributes = {"brand": "Nicolas", "brand_wikidata": "Q3340012"}
    sitemap_urls = ["https://www.nicolas.com/robots.txt"]
    sitemap_follow = ["Store-fr-"]
    sitemap_rules = [(r"/fr/magasins/[^/]+/s/(\d+).html$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location = json.loads(response.xpath("//@data-stores").get())["store0"]
        item = DictParser.parse(location)
        item["ref"] = item.pop("name")
        item["street_address"] = item.pop("addr_full", "")
        item["branch"] = location["displayName"]

        item["website"] = response.url
        item["email"] = response.xpath('//a[contains(@href, "mailto:")]/@href').get(default="").removeprefix("mailto:")
        extract_phone(item, response)

        yield item
