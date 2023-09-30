import scrapy

from locations.items import Feature


class DairyQueenSpider(scrapy.Spider):
    name = "dairyqueen"
    item_attributes = {"brand": "Dairy Queen", "brand_wikidata": "Q1141226"}
    allowed_domains = ["www.dairyqueen.com"]

    def start_requests(self):
        yield scrapy.Request(
            "https://prod-dairyqueen.dotcmscloud.com/api/es/search",
            method="POST",
            headers={
                "content-type": "application/json",
                "accept": "application/json",
                "referer": "https://www.dairyqueen.com/",
            },
            body='{"size":10000,"query":{"bool":{"must":[{"term":{"contenttype":"locationDetail"}}]}}}',
        )

    def parse(self, response):
        data = response.json()

        for store in data["contentlets"]:
            lat, lon = store.get("latlong", ",").split(",", 2)

            properties = {
                "name": f'{store["address1"]} ({store["conceptType"]})',
                "street_address": store.get("address3"),
                "phone": store.get("phone"),
                "city": store.get("city"),
                "state": store.get("stateProvince"),
                "postcode": store.get("postalCode"),
                "ref": store.get("storeId"),
                "website": "https://www.dairyqueen.com" + store.get("urlTitle"),
                "country": store.get("country"),
                "lat": lat,
                "lon": lon,
            }

            yield Feature(**properties)
