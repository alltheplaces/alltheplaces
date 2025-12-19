from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class ContinentePTSpider(Spider):
    name = "continente_pt"
    start_urls = ["https://prod.limmia-continente-public-api.com/localsPages/listLocalsPages"]

    brands = [
        {"brand": "Continente Bom Dia", "brand_wikidata": "Q123570507"},
        {"brand": "Continente Modelo", "brand_wikidata": "Q1892188"},
        {"brand": "Continente", "brand_wikidata": "Q2995683"},
    ]

    def parse(self, response, **kwargs):
        for location in response.json()["response"]["locations"]:
            if location["name"].startswith("MAXMAT "):
                continue

            item = DictParser.parse(location)

            item["street_address"] = location["streetAndNumber"]

            item["opening_hours"] = OpeningHours()
            for rule in location["openingHours"]:
                to_time = rule["to1"].replace(":030", ":30").replace(":000", ":00")
                item["opening_hours"].add_range(DAYS[rule["dayOfWeek"] - 1], rule["from1"], to_time)

            for photo in location["photos"]:
                if photo["type"] == "MAIN":
                    item["image"] = photo["publicUrl"]
                    break

            for brand in self.brands:
                if item["name"].startswith(brand["brand"]):
                    item.update(brand)
                    item["branch"] = item.pop("name").removeprefix(item["brand"])
                    break

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
