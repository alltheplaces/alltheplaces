import scrapy
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.avia_de import AVIA_SHARED_ATTRIBUTES


class AviaFRSpider(Spider):
    name = "avia_fr"
    item_attributes = AVIA_SHARED_ATTRIBUTES

    def start_requests(self):
        url = "https://www.avia-france.fr/wp-admin/admin-ajax.php"
        payload = "action=get_csv_data&columns%5B%5D=UID&columns%5B%5D=geo_lat&columns%5B%5D=geo_long&columns%5B%5D=Additional+Company+Info&columns%5B%5D=legal+type+of+company&columns%5B%5D=Street&columns%5B%5D=House+number&columns%5B%5D=ZIP+Code&columns%5B%5D=Place&columns%5B%5D=Telephone+No.&columns%5B%5D=mon_from_till&columns%5B%5D=tue_from_till&columns%5B%5D=wed_from_till&columns%5B%5D=thu_from_till&columns%5B%5D=fri_from_till&columns%5B%5D=sat_from_till&columns%5B%5D=sun_from_till&columns%5B%5D=Gonflage&columns%5B%5D=garage&columns%5B%5D=rent_of_cars&columns%5B%5D=truck_station&columns%5B%5D=gantry+car+wash&columns%5B%5D=Jetwash&columns%5B%5D=bistro&columns%5B%5D=Ad+blue+pomp&columns%5B%5D=outdoor_children_games&columns%5B%5D=adblue"
        yield scrapy.Request(
            url=url,
            method="POST",
            body=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
            callback=self.parse,
        )

    def parse(self, response, **kwargs):
        for store in response.json()["data"]:
            store["lon"] = store.pop("geo_long")
            store["lat"] = store.pop("geo_lat")
            store["postcode"] = store.pop("ZIP Code")
            item = DictParser.parse(store)
            item["ref"] = store.get("UID")
            item["name"] = store.get("Additional Company Info")
            item["state"] = store.get("Place")
            item["phone"] = store.get("Telephone No.")
            item["website"] = "https://www.avia-france.fr/"
            apply_category(Categories.FUEL_STATION, item)
            yield item
