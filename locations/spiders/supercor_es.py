from hashlib import sha1

from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_ES, OpeningHours


class SupercorESSpider(Spider):
    name = "supercor_es"
    item_attributes = {"brand": "Supercor", "brand_wikidata": "Q6135841", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["www.supercor.es"]
    start_urls = ["https://www.supercor.es/tiendas/"]

    def parse(self, response):
        js_blob = response.xpath('//script[contains(text(), "var tiendas = `")]/text()').get()
        js_blob = js_blob.split("var tiendas = `", 1)[1].split("`;", 1)[0]
        locations = parse_js_object(js_blob, unicode_escape=True)
        for location in locations:
            # Ignore closed stores
            if location["abierto"] != "1":
                continue

            item = DictParser.parse(location)
            # Create a reference ID from the store address as this is the most
            # permanent identifier available to be used.
            item["ref"] = sha1(location["direccion"].encode("UTF-8")).hexdigest()
            item["postcode"] = location["cp"]

            hours_text = " ".join(location["horario"]).replace(":|", ": ")
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_text, days=DAYS_ES)

            yield item
