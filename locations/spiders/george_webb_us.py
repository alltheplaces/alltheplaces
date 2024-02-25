from scrapy.spiders import XMLFeedSpider

from locations.categories import Categories
from locations.items import Feature


class GeorgeWebbUSSpider(XMLFeedSpider):
    name = "george_webb_us"
    item_attributes = {"brand": "George Webb", "brand_wikidata": "Q5546110", "extras": Categories.FAST_FOOD.value}
    allowed_domains = ["georgewebb.com"]
    start_urls = ["https://georgewebb.com/hwstorelocation/storeload"]
    iterator = "xml"
    itertag = "marker"

    def parse_node(self, response, node):
        properties = {
            "ref": node.xpath(".//@phone").get(),
            "name": node.xpath(".//@name").get(),
            "street_address": node.xpath(".//@address").get(),
            "city": node.xpath(".//@city").get(),
            "state": node.xpath(".//@state").get(),
            "country": node.xpath(".//@country").get(),
            "lat": node.xpath(".//@lat").get(),
            "lon": node.xpath(".//@lng").get(),
            "phone": node.xpath(".//@phone").get(),
            "email": node.xpath(".//@email").get(),
        }
        yield Feature(**properties)
