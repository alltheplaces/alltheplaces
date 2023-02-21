from scrapy import Spider

from locations.items import Feature

# Confusingly, not just IT but most of Europe
# Also not just Q8Italia


class Q8ItaliaSpider(Spider):
    name = "q8_italia"
    item_attributes = {"brand": "Q8", "brand_wikidata": "Q1634762"}
    start_urls = ["https://www.q8.it/geolocalizzatore/pv/all"]

    BRANDS = {
        "TANGO": None,  # TangoSpider
        "AUTOMAT": {"brand": "Q8 Easy", "brand_wikidata": "Q1806948"},
        # All others Q8
    }

    def parse(self, response, **kwargs):
        for location in response.json():
            # Note more? details available at:
            # https://www.q8.it/geolocalizzatore/pv/00PV000158

            item = Feature()
            item["ref"] = location["codice"]
            item["street_address"] = location["indirizzo"]
            item["city"] = location["localita"]
            item["state"] = location["provincia"]
            item["postcode"] = location["cap"]
            item["lat"] = location["latitudine"]
            item["lon"] = location["longitudine"]

            b = location["tipologie"][0]["tipologia"]
            if b == "TANGO":
                continue  # TangoSpider

            if brand := self.BRANDS.get(b):
                item.update(brand)

            # TODO: payments
            # pagamenti
            # digitali
            # sblocco
            # TODO: services
            # servizi
            # TODO: products
            # prodotti

            yield item
