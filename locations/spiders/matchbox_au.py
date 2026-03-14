import chompjs
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MatchboxAUSpider(Spider):
    name = "matchbox_au"
    item_attributes = {"brand": "Matchbox", "brand_wikidata": "Q117854120"}
    allowed_domains = ["matchbox.com.au"]
    start_urls = ["https://matchbox.com.au/pages/store-locator"]

    def parse(self, response):
        data_json = chompjs.parse_js_object(response.xpath("//script[@data-store-locator-json]/text()").get())
        for location in data_json.values():
            item = DictParser.parse(location)
            item["website"] = "https://matchbox.com.au" + item["website"]
            if location["lat"] not in ['Number("Matchbox Kitchenware Store - Greensborough")', 'Number("DFO Perth")']:
                item["lat"] = float(location["lat"].replace('Number("', "").replace('")', ""))
            item["lon"] = float(location["long"].replace('Number("', "").replace('")', ""))
            if location.get("hours"):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(location["hours"].replace("<br />", ""))
            apply_category(Categories.SHOP_HOUSEWARE, item)
            yield item
