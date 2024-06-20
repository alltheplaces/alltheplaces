from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class KrispyKrunchyChickenUSSpider(SitemapSpider):
    name = "krispy_krunchy_chicken_us"
    item_attributes = {"brand_wikidata": "Q65087447"}
    sitemap_urls = ["https://www.krispykrunchy.com/robots.txt"]
    sitemap_follow = ["wpsl_stores"]
    sitemap_rules = [(r"/locations/([^/]+)/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = chompjs.parse_js_object(
            response.xpath('//script[@id="wpsl-js-js-extra"]/text()').re_first(r"wpslMap_0 = ({.+})")
        )
        for location in data["locations"]:
            item = DictParser.parse(location)
            item["addr_full"] = None
            item["street_address"] = merge_address_lines([location["address"], location["address2"]])
            item["branch"] = location["store"]
            item["website"] = response.url

            yield item
