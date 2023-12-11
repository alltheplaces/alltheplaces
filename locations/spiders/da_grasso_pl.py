from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range


class DaGrassoPLSpider(Spider):
    name = "da_grasso_pl"
    item_attributes = {"brand": "Da Grasso", "brand_wikidata": "Q11692586"}
    start_urls = ["https://www.dagrasso.pl/api/v1/restaurant_list"]

    def parse(self, response, **kwargs):
        for feature in response.json():
            if feature["isMenu"]:
                continue
            feature["street_address"] = feature["street"]
            del feature["street"]
            item = DictParser.parse(feature)
            item["phone"] = ";".join(
                [feature[key] for key in ["phone", "phone2", "phone3", "mobilePhone"] if feature[key]]
            )
            opening_hours = OpeningHours()
            for hours in feature["workingHours"]:
                opening_hours.add_days_range(
                    days=day_range(hours["from"], hours["to"] or hours["from"]),
                    open_time=hours["open"],
                    close_time=hours["close"],
                )
            item["opening_hours"] = opening_hours
            yield item
