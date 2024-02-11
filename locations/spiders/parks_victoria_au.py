from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ParksVictoriaAUSpider(Spider):
    name = "parks_victoria_au"
    item_attributes = {"state": "Victoria", "operator": "Parks Victoria", "operator_wikidata": "Q3365478"}
    allowed_domains = ["www.parks.vic.gov.au"]
    start_urls = ["https://www.parks.vic.gov.au/where-to-stay/camping"]

    def parse(self, response):
        js_blob = response.xpath('//script[contains(text(), "var multipinmap_data_")]/text()').get()
        js_blob = "[{" + js_blob.split(" = [{", 1)[1].split("}];", 1)[0] + "}]"
        for location in parse_js_object(js_blob):
            item = DictParser.parse(location)
            apply_category(Categories.TOURISM_CAMP_SITE, item)
            apply_category({"reservation": "required"}, item)
            item["ref"] = item["website"] = location["url"].replace("http://", "https://")
            item["image"] = "https://www.parks.vic.gov.au" + location["mapImage"]
            yield item
