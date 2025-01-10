import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_IT, OpeningHours
from locations.items import set_closed


class PrixQualityITSpider(scrapy.Spider):
    name = "prix_quality_it"
    start_urls = [
        # Utilises Wordpress' Advanced Custom Fields. Unfortunately this means little commonality in types or fields,
        # beyond using a DictParser in the "acf" record and some of the url patterns
        "https://www.prixquality.com/wp-json/acf/v3/shop?per_page=999&orderby=title",
    ]
    time_format = "%H:%M"
    item_attributes = {"brand": "Prix Quality", "brand_wikidata": "Q61994819"}

    def parse(self, response):
        for record in response.json():
            store = record["acf"]
            item = DictParser.parse(store)
            item["ref"] = store["shop_code"]
            item["name"] = store["shop_name"]
            item["street_address"] = item.pop("addr_full")

            item["opening_hours"] = OpeningHours()
            for day in DAYS_IT:
                if times := store.get(day.lower(), ""):
                    if "CHIUSO" in times:
                        item["opening_hours"].set_closed(DAYS_IT[day])
                    else:
                        for time in times.split("|"):
                            item["opening_hours"].add_range(
                                DAYS_IT[day], *time.split("-"), time_format=self.time_format
                            )
            yield item
