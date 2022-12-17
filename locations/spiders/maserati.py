import scrapy

from locations.items import GeojsonPointItem


class MaseratiSpider(scrapy.Spider):
    name = "maserati"
    item_attributes = {
        "brand": "Maserati",
        "brand_wikidata": "Q26678",
    }
    allowed_domains = ["maserati.com"]
    start_urls = [
        "https://api.onthemap.io/server/v1/api/location?query=([sales]=[true] OR [assistance]=[true])&language=en&key=6e0b94fb-7f95-11ec-9c36-eb25f50f4870&channel=www.maserati.com",
    ]

    def parse(self, response):
        for row in response.json().get("data", {}).get("results", {}).get("features"):
            properties = {
                "ref": row.get("properties", {}).get("otm_id"),
                "name": row.get("properties", {}).get("dealername"),
                "country": row.get("properties", {}).get("countryIsoCode2"),
                "city": row.get("properties", {}).get("city"),
                "lat": row.get("geometry", {}).get("coordinates")[1],
                "lon": row.get("geometry", {}).get("coordinates")[0],
                "phone": row.get("properties", {}).get("phone"),
                "email": row.get("properties", {}).get("emailAddr"),
                "street_address": row.get("properties", {}).get("address"),
                "postcode": row.get("properties", {}).get("postcode"),
                "website": row.get("properties", {}).get("url"),
            }

            yield GeojsonPointItem(**properties)
