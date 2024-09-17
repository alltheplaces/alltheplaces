from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser


class BobaliESITSpider(Spider):
    name = "bobali_es_it"
    item_attributes = {"brand": "Boboli", "brand_wikidata": "Q39073733", "extras": Categories.SHOP_CLOTHES.value}
    start_urls = ["https://www.boboli.es/es/tiendas?all=1"]

    def start_requests(self):
        yield JsonRequest(url=self.start_urls[0])

    def parse(self, response):
        for location in response.json():
            if location["active"] == "1":
                # Example
                # {'id_store': '45', 'id_country': '6', 'id_state': '53', 'city': 'A CORUÑA', 'postcode': '15009', 'latitude': '43.35379410', 'longitude': '-8.40185850', 'phone': '+34981281297', 'fax': '', 'email': 'acoruna@boboli.es', 'active': '1', 'date_add': '2013-05-27 13:03:57', 'date_upd': '2024-08-27 03:08:23', 'store_identifier': '45', 'b2b_id': 'B2B_15096', 'type': '1', 'store_type': 'offline', 'postcode_influence': '', 'close': '0', 'show_store': '1', 'id_address': '1', 'country': 'España', 'address1': 'C/ POSSE, 51 ', 'address2': '', 'storeName': 'boboli A Coruña', 'note': '', 'stateName': 'A Coruña', 'state': 'CR', 'address_format': "<div class='row py-3 px-3'><div class='col-12 px-3 py-3 position-relative'><div class='row content-store'><div class='col-2 text-end'><i class='boboli-icon-store'></i></div><div class='col-10 pt-3'><div><strong>boboli A Coruña</strong></div><br>C/ POSSE, 51  <br>15009 A CORUÑA<br> A Coruña</div></div><div class='row footer-store mt-4 align-items-end'><div class='col-2 text-end'><i class='boboli-icon-phone'></i></div><div class='col-4 pt-2'>+34981281297</div><div class='col-2 text-end'></div><div class='col-4 pt-2'><a target='_blank' href='http://maps.google.com/maps?saddr=&daddr=(43.35379410,-8.40185850)'><i class='boboli-icon-pointer_map'></i> Ver mapa</a></div></div></div></div></div>"}
                item = DictParser.parse(location)
                item["ref"] = location["id_store"]
                # TODO: location['store_type'] == 'offline' - is this an indicator of being in a department store?
                yield item
