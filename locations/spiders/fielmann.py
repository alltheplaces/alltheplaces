import json

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class FielmannSpider(SitemapSpider):
    name = "fielmann"
    item_attributes = {"brand": "Fielmann", "brand_wikidata": "Q457822"}
    sitemap_urls = [
        "https://www.fielmann.de/de-de/stores_details01.xml",
        "https://www.fielmann.at/de-at/stores_details01.xml",
        "https://www.fielmann.ch/de-ch/stores_details01.xml",
        "https://www.fielmann.pl/pl-pl/stores_details01.xml",
        "https://www.fielmann.cz/cs-cz/stores_details01.xml",
        # the following urls need a different parsing
        # "https://optika-fielinn.by",
        # "https://www.fielmann.lu",
        # "https://www.fielmann.it",
        # "https://www.fielmann.lt/",
        # "https://www.fielmann.lv/",
        # "https://optika-fielmann.ua/",
        # "https://www.opticauniversitaria.es/",
        # "https://www.clarus.si/",
    ]
    sitemap_rules = [("", "parse_store")]

    def parse_store(self, response):
        ldjson = response.xpath('//script[@type="application/ld+json"]/text()[contains(.,"@context")]')[1].get()

        if ldjson is None:
            return

        data = json.loads(ldjson)

        hours = OpeningHours()
        if data["openingHoursSpecification"] is not None:
            for row in data["openingHoursSpecification"]:
                day = row["dayOfWeek"][0]
                hours.add_range(day, row["opens"], row["closes"], "%H:%M")

        properties = {
            "ref": data["url"].split("/")[-2],
            "name": data["name"],
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "street_address": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "opening_hours": hours.as_opening_hours(),
            "website": data["url"],
            "phone": data["contactPoint"]["telephone"],
        }

        yield Feature(**properties)
