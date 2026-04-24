from urllib.parse import urljoin

import scrapy

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser


class VkusnoITochkaRUSpider(scrapy.Spider):
    """
    A spider for russian fast-food chain "Vkusno i tochka". It has 863 locations as of 2023-01-09.
    Main Url: https://vkusnoitochka.ru/
    Data url: https://vkusnoitochka.ru/api/restaurants
    Data format: json
    """

    name = "vkusno_i_tochka_ru"
    item_attributes = {"brand": "Вкусно — и точка", "brand_wikidata": "Q112406961"}
    all_restaurants_url = "https://vkusnoitochka.ru/api/restaurants"
    single_restaurant_url = "https://vkusnoitochka.ru/api/restaurant/"
    restaurants_map_url = "https://vkusnoitochka.ru/restaurants/map/"
    start_urls = [all_restaurants_url]

    def parse(self, response, **kwargs):
        for _, restaurant in response.json()["restaurants"].items():
            url = urljoin(self.single_restaurant_url, str(restaurant["id"]))
            yield scrapy.Request(
                url,
                callback=self.parse_restaurant,
                cb_kwargs=dict(coordinates=(restaurant["latitude"], restaurant["longitude"])),
            )

    def parse_restaurant(self, response, coordinates):
        restaurant = response.json()["restaurant"]
        restaurant["latitude"] = coordinates[0]
        restaurant["longitude"] = coordinates[1]
        restaurant["housenumber"] = restaurant.get("house")
        restaurant["website"] = urljoin(self.restaurants_map_url, str(restaurant["id"]))
        item = DictParser.parse(restaurant)
        features = [f["xmlId"] for f in restaurant["features"]]
        apply_yes_no(Extras.DRIVE_THROUGH, item, "mcauto" in features, True)
        if opening_hours := restaurant.get("openingHours"):
            item["opening_hours"] = self.parse_hours(opening_hours)
        return item

    def parse_hours(self, hours):
        """
        Parse opening hours.
        Input format example:
          [
            {'name': '06:30—00:00', 'from': '06:30', 'until': '00:00', 'type': 1, 'weekday': 1},
            {'name': '06:30—00:00', 'from': '06:30', 'until': '00:00', 'type': 1, 'weekday': 7},
            {'name': '05:00—10:00', 'from': '05:00', 'until': '10:00', 'type': 2, 'weekday': 1},
            {'name': '05:00—10:00', 'from': '05:00', 'until': '10:00', 'type': 2, 'weekday': 7},
          ]
        Type 1 is for lobby hours which is what we want.
        Weekday 1 is for all days of the week.
        """
        hours = [x for x in hours if x["weekday"] == 1 and x["type"] == 1]
        if not hours:
            return None

        if len(hours) == 1:
            return "Mo-Su " + hours[0]["from"] + "-" + hours[0]["until"]
        if len(hours) > 1:
            days = "Mo-Su "
            for hour in hours:
                days += hour["from"] + "-" + hour["until"] + ","
            return days[:-1]
