from scrapy import Spider

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class InverSpider(Spider):
    name = "inver"
    item_attributes = {"brand": "Inver", "brand_wikidata": "Q112579016"}
    start_urls = [
        "https://inverenergy.ie/wp-admin/admin-ajax.php?action=get_station_data",
        "https://inverenergy.ie/canada/wp-admin/admin-ajax.php?action=get_station_data",
    ]

    def parse(self, response, **kwargs):
        for location in response.json()["data"]:
            item = DictParser.parse(location)

            apply_yes_no(Extras.TOILETS, item, "toilet" in location["services"])
            apply_yes_no(Extras.ATM, item, "atm" in location["services"])
            apply_yes_no(Extras.CAR_WASH, item, "carwash" in location["services"])
            apply_yes_no(Fuel.ADBLUE, item, "adblue" in location["services"])
            apply_yes_no("hgv", item, "hgv_access" in location["services"])

            if "convenience_store" in location["services"]:
                apply_category(Categories.SHOP_CONVENIENCE, item)
            apply_category(Categories.FUEL_STATION, item)

            item["ref"] = f'{item["country"]}-{item["ref"]}'

            yield item
