from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CobasiBRSpider(Spider):
    name = "cobasi_br"
    item_attributes = {"brand_wikidata": "Q86739236"}
    start_urls = ["https://mid-back.cobasi.com.br/stores"]

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["website"] = "https://www.cobasi.com.br/lojas/" + item["website"]
            item["phone"] = location.get("whatsAppShopPhone")
            if image := location.get("image"):
                image = image.replace("http://", "https://")
                item["image"] = image
            item["ref"] = location["_id"]
            # 'shopBusinessHours': {'weekdays': '10h00 às 21h45 ', 'saturday': '10h00 às 21h45 ', 'sunday': '12h00 às 21h00', 'holiday': '12h00 às 21h00'},
            item["opening_hours"] = OpeningHours()
            for days, hours in location["shopBusinessHours"].items():
                item["opening_hours"].add_ranges_from_string(
                    days.replace("weekdays", "Mo-Fr") + " " + hours.replace(" às ", "-").replace("h", ":"),
                )

            if "Loja teste" not in item.get("name"):
                yield item
