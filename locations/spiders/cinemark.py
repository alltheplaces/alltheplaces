from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.react_server_components import parse_rsc


class CinemarkSpider(SitemapSpider):
    name = "cinemark"
    item_attributes = {"brand": "Cinemark", "brand_wikidata": "Q707530"}
    allowed_domains = ["cinemark.com"]
    sitemap_urls = ["https://www.cinemark.com/sitemap.xml"]
    sitemap_rules = [(r"/theatres/[^/]+/[^/]+$", "parse")]
    custom_settings = {"DOWNLOAD_DELAY": 10}  # Requested by robots.txt

    def parse(self, response: Response, **kwargs: Any) -> Any:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        rsc = "".join(s for _, s in (chompjs.parse_js_object(script) for script in scripts) if isinstance(s, str))
        location = self.find_theatre(dict(parse_rsc(rsc.encode())))
        if not location or location["status"] == "Closed Permanently":
            return

        item = DictParser.parse(location)
        item["ref"] = location["theaterId"]
        item["name"] = location["theaterName"]
        item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
        item["phone"] = location["officePhone"]
        item["website"] = response.url
        apply_category(Categories.CINEMA, item)
        yield item

    def find_theatre(self, node: Any) -> dict | None:
        if isinstance(node, dict):
            if "theaterId" in node and "latitude" in node:
                return node
            node = list(node.values())
        if isinstance(node, list):
            for value in node:
                if theatre := self.find_theatre(value):
                    return theatre
        return None
