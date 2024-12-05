import json
from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser


class McgrathAUSpider(SitemapSpider):
    name = "mcgrath_au"
    item_attributes = {
        "brand_wikidata": "Q105290661",
        "brand": "McGrath",
    }
    sitemap_urls = ["https://www.mcgrath.com.au/sitemap/offices.xml"]
    sitemap_rules = [(r"/offices/[-\w]+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # coordinates are available in the JSON Blob only.
        office = json.loads(
            chompjs.parse_js_object(response.xpath('//script[contains(text(),"coordinates")]/text()').get())[-1].split(
                ":", 1
            )[-1]
        )[0][-1]["profile"]
        item = DictParser.parse(office)
        item["branch"] = item.pop("name")
        item["website"] = response.url
        yield item
