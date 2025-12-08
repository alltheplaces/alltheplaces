from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import XMLFeedSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class OkNLSpider(XMLFeedSpider):
    name = "ok_nl"
    item_attributes = {"brand": "OK", "brand_wikidata": "Q123472183"}
    start_urls = ["https://ok.nl/wp-json/tankstations/v1/kml"]
    iterator = "xml"
    itertag = "kml/Document/Placemark"

    def parse_node(self, response: Response, selector: Selector):
        item = Feature()
        item["branch"] = selector.xpath("name/text()").get().removeprefix("OK").strip()
        item["ref"] = item["website"] = selector.xpath("url/text()").get()
        item["lon"], item["lat"], _ = selector.xpath("Point/coordinates/text()").get().split(", ")

        apply_category(Categories.FUEL_STATION, item)

        yield item
