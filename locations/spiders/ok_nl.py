from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import XMLFeedSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class OkNLSpider(XMLFeedSpider):
    name = "ok_nl"
    start_urls = ["https://ok.nl/wp-json/tankstations/v1/kml"]
    iterator = "xml"
    itertag = "kml/Document/Placemark"

    BRAND_MAPPING = {
        "#ok": {"brand": "OK", "brand_wikidata": "Q123472183"},
        "#bp": {"brand": "BP", "brand_wikidata": "Q152057"},
    }

    def parse_node(self, response: Response, selector: Selector):
        item = Feature()

        style_url = selector.xpath("styleUrl/text()").get()
        brand_info = self.BRAND_MAPPING.get(style_url)

        if brand_info:
            item.update(brand_info)
            name = selector.xpath("name/text()").get()
            item["branch"] = name.removeprefix(brand_info["brand"]).strip()
        else:
            self.crawler.stats.inc_value(f"atp/brand/unmapped/{style_url}")

        item["ref"] = item["website"] = selector.xpath("url/text()").get()
        item["lon"], item["lat"], _ = selector.xpath("Point/coordinates/text()").get().split(", ")

        apply_category(Categories.FUEL_STATION, item)

        yield item
