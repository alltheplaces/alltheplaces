# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class TacocabanaSpider(scrapy.Spider):
    name = "tacocabana"
    item_attributes = {"brand": "Taco Cabana", "brand_wikidata": "Q12070488"}
    allowed_domains = ["api.koala.fuzzhq.com"]

    def start_requests(self):
        yield scrapy.http.JsonRequest(
            "https://api.koala.fuzzhq.com/oauth/access_token",
            data={
                "client_id": "3nA4STkGif0fZGApqxMlVewy3h8HN6Fsy7jVOACP",
                "client_secret": "8oBU5gWiNg04zYzz61hN3ETrTIzvmbGyeLCX0F1s",
                "grant_type": "ordering_app_credentials",
                "scope": "group:ordering_app",
            },
            callback=self.fetch_locations,
        )

    def fetch_locations(self, response):
        self.access_token = response.json()["access_token"]
        yield self.request(
            "https://api.koala.fuzzhq.com/v1/ordering/store-locations/?include[]=operating_hours&include[]=attributes&per_page=50"
        )

    def request(self, url):
        return scrapy.Request(
            url, headers={"Authorization": f"Bearer {self.access_token}"}
        )

    def parse(self, response):
        data = response.json()

        for store in data["data"]:
            properties = {
                "website": f'https://olo.tacocabana.com/menu/{store["slug"]}?showInfoModal=true',
                "ref": store["brand_id"],
                "lat": store["latitude"],
                "lon": store["longitude"],
                "addr_full": store["street_address"],
                "city": store["city"],
                "state": store["cached_data"]["state"],
                "country": store["country"],
                "postcode": store["zip_code"],
                "phone": store["phone_number"],
            }
            yield GeojsonPointItem(**properties)

        next_url = data["meta"]["pagination"]["links"]["next"]
        if next_url:
            yield self.request(next_url)
