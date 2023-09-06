import scrapy

from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature


class MatchFRSpider(scrapy.Spider):
    name = "match_fr"
    item_attributes = {"brand": "Match", "brand_wikidata": "Q513977"}
    start_urls = ["https://api-drive.drive.supermarchesmatch.fr/sites_searches"]
    requires_proxy = True

    def parse(self, response):
        stores = response.json()["data"]
        for store in stores:
            item = Feature()
            attributes = store["attributes"]["site"]
            item["ref"] = store["attributes"]["_id"]
            item["phone"] = attributes["telephone"]
            item["lon"] = attributes["longitude"]
            item["lat"] = attributes["latitude"]
            item["postcode"] = attributes["codePostal"]
            item["city"] = attributes["ville"]
            item["name"] = attributes["libelleLong"]
            item["street_address"] = " ".join(
                [attributes["adresse1"] or "", attributes["adresse2"] or "", attributes["adresse3"] or ""]
            ).strip()
            item["opening_hours"] = self.parse_opening_hours(store)
            yield item

    def parse_opening_hours(self, store):
        oh = OpeningHours()

        for day in ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]:
            opening_hours = store["attributes"]["site"]["horaire" + day]
            oh.add_ranges_from_string(ranges_string=day + " " + opening_hours, days=DAYS_FR)

        return oh.as_opening_hours()
