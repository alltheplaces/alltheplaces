from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.hours import DAYS_ES, DELIMITERS_ES, OpeningHours
from locations.items import Feature


class GadisaESSpider(Spider):
    name = "gadisa_es"
    allowed_domains = ["www.gadisa.es"]
    start_urls = [
        "https://www.gadisa.es/api/centro/sec::cashifa",
        "https://www.gadisa.es/api/centro/sec::claudio",
        "https://www.gadisa.es/api/centro/sec::gadis",
    ]
    brands = {
        "CASACLAUDIO": {"brand": "Casa Claudio", "brand_wikidata": "Q123370107", "extras": {"shop": "deli"}},
        "CASHIFA": {"brand": "Cash IFA", "brand_wikidata": "Q123369964", "extras": Categories.SHOP_WHOLESALE.value},
        "CLAUDIO": {"brand": "Claudio", "brand_wikidata": "Q123369953", "extras": Categories.SHOP_SUPERMARKET.value},
        "GADIS": {"brand": "Gadis", "brand_wikidata": "Q114398305", "extras": Categories.SHOP_SUPERMARKET.value},
    }

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            if location["coordenada"] == "0,0":
                # Invalid location
                continue
            properties = {
                "ref": location["id"],
                "name": location["nombre"],
                "lat": location["coordenada"].split(",", 1)[0],
                "lon": location["coordenada"].split(",", 1)[1],
                "street_address": location["dir"],
                "city": location["pob"],
                "state": location["prov"],
                "postcode": location["cp"],
                "phone": location.get("tel"),
                "opening_hours": OpeningHours(),
            }
            properties.update(self.brands[location["sec"]])
            if location.get("horario"):
                properties["opening_hours"].add_ranges_from_string(
                    ranges_string=location["horario"], days=DAYS_ES, delimiters=DELIMITERS_ES
                )
            yield Feature(**properties)
