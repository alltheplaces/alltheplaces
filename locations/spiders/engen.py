import scrapy

from locations.categories import Categories, Fuel, apply_yes_no
from locations.dict_parser import DictParser


class EngenSpider(scrapy.Spider):
    name = "engen"
    item_attributes = {"brand": "Engen", "brand_wikidata": "Q3054251", "extras": Categories.FUEL_STATION.value}
    allowed_domains = ["engen.co.za"]
    start_urls = ["https://engen-admin.engen.co.za/api/service-stations/all"]

    def parse(self, response):
        data = response.json()
        for i in data["response"]["data"]["stations"]:
            i["branch"] = i.pop("company_name").replace(self.item_attributes["brand"], "").strip()
            i["phone"] = i.pop("mobile")
            postcode = i.pop("street_postal_code")
            if postcode and postcode != "0":
                i["postcode"] = postcode
            item = DictParser.parse(i)
            apply_yes_no(Fuel.ADBLUE, item, "AdBlue" in i["rental_units"])
            yield item
