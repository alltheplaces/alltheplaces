from typing import Any

from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import XMLFeedSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class GeorgeWebbUSSpider(XMLFeedSpider):
    name = "george_webb_us"
    item_attributes = {"brand": "George Webb Restaurant", "brand_wikidata": "Q5546110"}
    allowed_domains = ["georgewebb.com"]
    start_urls = ["https://georgewebb.com/hwstorelocation/storeload"]
    iterator = "xml"
    itertag = "marker"

    def parse_node(self, response: Response, node: Selector) -> Any:
        properties = {
            "ref": node.xpath(".//@phone").get(),
            "street_address": node.xpath(".//@address").get(),
            "city": node.xpath(".//@city").get(),
            "state": node.xpath(".//@state").get(),
            "country": node.xpath(".//@country").get(),
            "lat": node.xpath(".//@lat").get(),
            "lon": node.xpath(".//@lng").get(),
            "phone": node.xpath(".//@phone").get(),
            "email": node.xpath(".//@email").get(),
        }
        item = Feature(**properties)
        apply_category(Categories.RESTAURANT, item)
        yield item
