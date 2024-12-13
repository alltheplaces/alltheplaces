from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class BiedronkaPLSpider(Spider):
    name = "biedronka_pl"
    item_attributes = {"brand": "Biedronka", "brand_wikidata": "Q857182"}

    def start_requests(self):
        yield JsonRequest(
            "https://www.biedronka.pl/api/shop/shippingcenter", headers={"X-Requested-With": "XMLHttpRequest"}
        )

    def parse(self, response, **kwargs):
        for city in response.json()["items"]:
            yield JsonRequest(
                url=f'https://www.biedronka.pl/api/shop/cityshopsbyslug?slug={city["slug"]}',
                headers={"X-Requested-With": "XMLHttpRequest"},
                callback=self.parse_city,
            )

    def parse_city(self, response, **kwargs):
        for location in response.json()["items"]:
            location.pop("name")
            item = DictParser.parse(location)

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                if times := location.get(f"hours_{day.lower()}"):
                    if "-" in times:
                        start, end = times.split("-")
                        item["opening_hours"].add_range(day, start, end)

            apply_yes_no(Extras.ATM, item, location["atm"] == "1")
            apply_category(Categories.SHOP_SUPERMARKET, item)

            item["website"] = f'https://www.biedronka.pl/pl/shop,id,{location["id"]}'

            yield item
