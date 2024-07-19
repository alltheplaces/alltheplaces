import scrapy

from locations.items import Feature


class KorianFRSpider(scrapy.Spider):
    name = "korian_fr"
    item_attributes = {"brand": "Korian", "brand_wikidata": "Q3198944"}
    allowed_domains = ["api-www.korian.fr"]

    def start_requests(self):
        types = [
            "maison-retraite",
            "clinique-ssr",
            "residence-seniors",
            "hospitalisation-a-domicile",
        ]

        regions = [
            "bretagne",
            "occitanie",
            "ile-de-france",
            "normandie",
            "auvergne-rhone-alpes",
            "nouvelle-aquitaine",
            "hauts-de-france",
            "provence-alpes-cote-dazur",
            "centre-val-de-loire",
            "pays-de-la-loire",
            "bourgogne-franche-comte",
            "grand-est",
        ]

        for type in types:
            for region in regions:
                url = "https://api-www.korian.fr/api-front/FR/{type}/{region}".format(type=type, region=region)
                yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        result = response.json()

        stores = result["data"]["content"][0]["results"]

        for store in stores:
            properties = {
                "ref": store["id"],
                "name": store["name"],
                "street_address": store["address"],
                "city": store["city"],
                "state": store["region"],
                "postcode": store["zipcode"],
                "country": "FR",
                "lat": store["latitude"],
                "lon": store["longitude"],
                "website": "https://www.korian.fr/" + store["redirecturl"],
            }

            yield Feature(**properties)
