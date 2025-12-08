from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class TacoTimeCASpider(Spider):
    name = "taco_time_ca"
    item_attributes = {"brand": "Taco Time", "brand_wikidata": "Q7673969"}
    start_urls = [
        "https://tacotimecanada.com/wp-json/tacotime/v1/nearest-locations?latitude=51.36832201878928&longitude=-93.83436394713593&limit=1000"
    ]

    def parse(self, response):
        data = response.json()
        for shop in data:
            item = DictParser.parse(shop)
            item["ref"] = f'{shop.get("address")} {item.get("city")} {item.get("province")}, {item.get("postal_code")}'
            item["branch"] = shop.get("location")
            item["street_address"] = item.pop("addr_full")
            self.parse_opening_hours(shop.get("opening_hours"), item)

            yield item

    def parse_opening_hours(self, hours, item):
        try:
            opening_hours = OpeningHours()
            for day in hours:
                opening_hours.add_range(
                    day=day.get("title"),
                    open_time=day.get("text").split(" – ")[0],
                    close_time=day.get("text").split(" – ")[1],
                    time_format="%I:%M %p",
                )

            item["opening_hours"] = opening_hours
        except:
            self.crawler.stats.inc_value("failed_parsing_hours")
