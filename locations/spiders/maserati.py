import scrapy

from locations.items import GeojsonPointItem


class MaseratiSpider(scrapy.Spider):
    name = "maserati"
    item_attributes = {
        "brand": "maserati",
        "brand_wikidata": "Q26678",
    }
    allowed_domains = ["maserati.com"]
    start_urls = [
        "https://api.onthemap.io/server/v1/api/location?query=([sales]=[true] OR [assistance]=[true])&language=en&sort=dealername&key=6e0b94fb-7f95-11ec-9c36-eb25f50f4870&channel=www.maserati.com",
    ]

    def parse(self, response):
        for row in response.json()["data"]["results"]["features"]:
            properties = {
                "ref": row["properties"]["otm_id"],
                "name": row["properties"]["dealername"],
                "country": row["properties"]["countryIsoCode2"],
                "city": row["properties"]["city"],
                "lat": row["geometry"]["coordinates"][1],
                "lon": row["geometry"]["coordinates"][0],
                "phone": row["properties"]["phone"],
                "email": row["properties"]["emailAddr"],
                "street_address": row["properties"]["address"],
                "postcode": row["properties"]["postcode"],
                "website": row["properties"]["url"],
            }

            yield GeojsonPointItem(**properties)
