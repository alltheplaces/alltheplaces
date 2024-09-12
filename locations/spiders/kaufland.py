from scrapy import Spider

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature


class KauflandSpider(Spider):
    name = "kaufland"
    item_attributes = {"brand": "Kaufland", "brand_wikidata": "Q685967"}
    website_formats = {
        "https://www.kaufland.bg/.klstorefinder.json": "https://www.kaufland.bg/moyat-kaufland/uslugi/filiali/{}.html",
        "https://prodejny.kaufland.cz/.klstorefinder.json": "https://prodejny.kaufland.cz/aktualne/servis/prodejna/{}.html",
        "https://www.kaufland.hr/.klstorefinder.json": "https://www.kaufland.hr/usluge/poslovnica/{}.html",
        "https://www.kaufland.md/ro/.klstorefinder.json": "https://www.kaufland.md/ro/utile/magazin/{}.html",
        "https://sklep.kaufland.pl/.klstorefinder.json": "https://sklep.kaufland.pl/dla-klienta/sklepy/{}.html",
        "https://www.kaufland.ro/.klstorefinder.json": "https://www.kaufland.ro/utile/magazin/{}.html",
        "https://predajne.kaufland.sk/.klstorefinder.json": "https://predajne.kaufland.sk/servis/predajne/{}.html",
        "https://filiale.kaufland.de/.klstorefinder.json": "https://filiale.kaufland.de/service/filiale/{}.html",
    }
    start_urls = website_formats.keys()

    def parse(self, response, **kwargs):
        for location in response.json():
            item = Feature()

            item["ref"] = location["n"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            item["branch"] = location["cn"].removeprefix("KAUFLAND").removeprefix("Kaufland").strip(" -")
            item["phone"] = location["p"].replace("/", "")
            item["postcode"] = location["pc"]
            item["street_address"] = location["sn"]
            item["city"] = location["t"]
            item["extras"]["start_date"] = location["opd"]

            oh = OpeningHours()
            for rule in location["wod"]:
                day, start_time, end_time = rule.split("|")
                oh.add_range(day, start_time, end_time)
            item["opening_hours"] = oh

            item["website"] = self.website_formats.get(response.url).format(location["friendlyUrl"])

            services = location["slf"].split(",")
            apply_yes_no(Extras.TOILETS, item, "Barrier-freeWC" in services)
            apply_yes_no(Fuel.ELECTRIC, item, "EVChargingStation_normal" in services)

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
