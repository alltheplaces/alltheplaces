import scrapy
from scrapy import Spider

from locations.items import Feature


class WyconCosmeticsSpider(Spider):
    name = "wycon_cosmetics"
    item_attributes = {"brand": "Wycon Cosmetics", "brand_wikidata": "Q55831243"}

    def start_requests(self):
        yield scrapy.FormRequest(
            url="https://www.wyconcosmetics.com/index.php",
            formdata={
                "extension": "geo",
                "controller": "places",
                "action": "search_by_city",
                "depth": "1",
                "cityId": "2",
                "language": "EN",
                "zone": "eu",
                "version": "1026",
                "cookieVersion": "1",
                "ajax_referer": "https%3A%2F%2Fwww.wyconcosmetics.com%2Fen%2Fstores",
                "distance": "40000",
            },
            callback=self.parse,
            headers={
                "Referer": "https://www.wyconcosmetics.com/en/stores",
                "Origin": "https://www.wyconcosmetics.com",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
            },
        )

    def parse(self, response, **kwargs):
        for store in response.json()["payload"]["places"]:
            address = store["geoTag"]
            properties = {
                "ref": store["id"],
                "name": store["title"],
                "website": store["permalink"],
                "phone": store["phone"],
                "street_address": address["street_address"],
                "postcode": address["zipcode"],
                "city": address["cityName"],
                "country": address["countryName"],
                "lon": address["longitude"],
                "lat": address["latitude"],
            }
            yield Feature(**properties)
