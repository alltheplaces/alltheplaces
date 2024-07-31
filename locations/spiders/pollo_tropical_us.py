import chompjs
import scrapy

from locations.dict_parser import DictParser


class PolloTropicalUSSpider(scrapy.Spider):
    name = "pollo_tropical_us"
    allowed_domains = ["https://www.pollotropical.com/"]
    item_attributes = {"brand": "Pollo Tropical", "brand_wikidata": "Q3395356"}
    start_urls = ["https://www.pollotropical.com/locations"]

    def parse(self, response, **kwargs):
        data = chompjs.parse_js_object(response.xpath('//script[contains(text(), "locations")]').get())
        for location in DictParser.get_nested_key(data, "list"):
            location["state"] = location["cached_data"]["state"]
            item = DictParser.parse(location)

            item["website"] = "https://olo.pollotropical.com/menu/{}?showInfoModal=true".format(location["slug"])

            yield item
