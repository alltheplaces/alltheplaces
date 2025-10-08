from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_SR, OpeningHours


class A1RSSpider(Spider):
    name = "a1_rs"
    item_attributes = {"brand_wikidata": "Q826186"}
    allowed_domains = ["a1.rs"]
    start_urls = ["https://a1.rs/o-a1/prodaja/prodajna_mesta_mapa"]

    def parse(self, response):
        cities_js = (
            response.xpath('//script[contains(text(), "var cities_json = ")]/text()')
            .get()
            .split("var cities_json = ", 1)[1]
            .split("}];", 1)[0]
            + "}]"
        )
        cities_dict = parse_js_object(cities_js)
        for city in cities_dict:
            yield JsonRequest(
                url=f'https://a1.rs/sr_latin/api/pos/get_cities?city_id={city["id"]}', callback=self.parse_city_list
            )

    def parse_city_list(self, response):
        for location in response.json():
            if location["name"] != "A1 Centar":
                # Ignore partner stores.
                continue
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full", None)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["working_hours"], days=DAYS_SR)
            yield item
