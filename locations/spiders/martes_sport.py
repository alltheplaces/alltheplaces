import json

from scrapy import Spider

from locations.dict_parser import DictParser


class MartesSportSpider(Spider):
    name = "martes_sport"
    item_attributes = {"brand": "Martes Sport", "brand_wikidata": "Q62073490"}
    start_urls = ["https://martessport.com.pl/en/our-stores/"]
    skip_auto_cc_domain = True

    def parse(self, response, **kwargs):
        data = json.loads(
            response.xpath('//script[contains(text(), "var data")]/text()').re_first(r"var data = (\{.*\});")
        )
        for store in json.loads(data["stores"]):
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["street_address"] = store["location_address"]
            item["postcode"] = store["location_zip"]
            item["city"] = store["location_city"]
            yield item
