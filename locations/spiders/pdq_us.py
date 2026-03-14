import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class PdqUSSpider(SitemapSpider):
    name = "pdq_us"
    item_attributes = {"brand": "PDQ", "brand_wikidata": "Q87675367"}
    sitemap_urls = ["https://www.eatpdq.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/(?!find-a-location).*", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location_data = json.loads(response.xpath("//@data-context").get())
        item = DictParser.parse(location_data["location"])
        item["lat"] = location_data["location"]["markerLat"]
        item["lon"] = location_data["location"]["markerLng"]
        item["addr_full"] = merge_address_lines([item["street_address"], location_data["location"]["addressLine2"]])
        item["ref"] = item["website"] = response.url
        yield item
