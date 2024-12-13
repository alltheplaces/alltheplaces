import scrapy

from locations.items import Feature


class WingstopGBSpider(scrapy.Spider):
    name = "wingstop_gb"
    item_attributes = {"brand": "Wingstop", "brand_wikidata": "Q8025339"}
    allowed_domains = ["www.wingstop.co.uk"]
    start_urls = ("https://api.wingstop.co.uk/restaurants/",)

    def parse_store(self, store_json):
        return Feature(
            lat=store_json["latitude"],
            lon=store_json["longitude"],
            name=store_json["name"],
            addr_full=store_json["streetaddress"],
            city=store_json["city"],
            state=store_json["state"],
            postcode=store_json["zip"],
            country=store_json["country"],
            phone=store_json["telephone"],
            website=store_json["url"],
            ref=store_json["id"],
        )

    def parse(self, response):
        response_dictionary = response.json()
        stores_array = response_dictionary["restaurants"]
        return list(map(self.parse_store, stores_array))
