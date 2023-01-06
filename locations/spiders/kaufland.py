import scrapy

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class KauflandSpider(scrapy.Spider):
    name = "kaufland"
    item_attributes = {"brand": "Kaufland", "brand_wikidata": "Q685967", "extras": Categories.SHOP_SUPERMARKET.value}
    website_formats = {
        "https://www.kaufland.bg/.klstorefinder.json": "https://www.kaufland.bg/moyat-kaufland/uslugi/filiali/{}.html",
        "https://www.kaufland.cz/.klstorefinder.json": "https://www.kaufland.cz/aktualne/servis/prodejna/{}.html",
        "https://www.kaufland.hr/.klstorefinder.json": "https://www.kaufland.hr/usluge/poslovnica/{}.html",
        "https://www.kaufland.md/ro/.klstorefinder.json": "https://www.kaufland.md/ro/utile/magazin/{}.html",
        "https://www.kaufland.pl/.klstorefinder.json": "https://www.kaufland.pl/dla-klienta/sklepy/{}.html",
        "https://www.kaufland.ro/.klstorefinder.json": "https://www.kaufland.ro/utile/magazin/{}.html",
        "https://www.kaufland.sk/.klstorefinder.json": "https://www.kaufland.sk/servis/predajne/{}.html",
        "https://filiale.kaufland.de/.klstorefinder.json": "https://filiale.kaufland.de/service/filiale/frankfurt-oder-spitzkrug-multi-center-{}.html",
    }
    start_urls = website_formats.keys()

    def parse(self, response, **kwargs):
        for location in response.json():
            item = GeojsonPointItem()

            item["ref"] = location["n"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            item["name"] = location["cn"]
            item["phone"] = location["p"].replace("/", "")
            item["postcode"] = location["pc"]
            item["street_address"] = location["sn"]
            item["city"] = location["t"]

            oh = OpeningHours()
            for rule in location["wod"]:
                day, start_time, end_time = rule.split("|")
                oh.add_range(day, start_time, end_time)
            item["opening_hours"] = oh.as_opening_hours()

            item["website"] = self.website_formats.get(response.url).format(location["friendlyUrl"])

            yield item
