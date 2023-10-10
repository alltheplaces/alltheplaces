import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature


class PocztaPolskaPLSpider(scrapy.Spider):
    name = "poczta_polska_pl"
    item_attributes = {"brand": "Poczta Polska", "brand_wikidata": "Q168833"}
    start_urls = ["https://placowki.poczta-polska.pl/ajax/getProvince/"]

    def parse(self, response, **kwargs):
        for province in response.json()["response"]:
            yield JsonRequest(
                url=f'https://placowki.poczta-polska.pl/ajax/getResultsByProvince/?province={province["id"]}',
                callback=self.parse_locations,
            )

    def parse_locations(self, response, **kwargs):
        for location in response.json()["response"]:
            item = Feature()
            item["ref"] = location.get("pni")
            item["name"] = location.get("nazwa")
            item["lat"] = location.get("y")
            item["lon"] = location.get("x")
            item["street_address"] = location.get("ulica")
            item["city"] = location.get("miejscowosc")
            item["state"] = location.get("wojewodztwo")
            item["postcode"] = location.get("kod")
            item["phone"] = ";".join(location.get("telefon")[0].split(","))
            apply_category(Categories.POST_OFFICE, item)
            # TODO: parse hours, services in 'opis' attributes
            yield item
