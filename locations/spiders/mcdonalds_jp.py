import scrapy

from locations.items import Feature


class McDonaldsJPSpider(scrapy.Spider):
    name = "mcdonalds_jp"
    item_attributes = {"brand_wikidata": "Q38076"}
    start_urls = (
        "https://map.mcdonalds.co.jp/api/poi?uuid=91b35ff7-e1ca-47b5-a0c0-377c41a6c3f2&bounds=-11.17840187371178%2C56.25%2C70.61261423801925%2C-146.25&_=1513674348668",
    )

    def parse(self, response):
        results = response.json()
        for data in results:
            properties = {
                "ref": data["id"],
                "addr_full": data["address"],
                "name": data["name"],
                "lat": data["latitude"],
                "lon": data["longitude"],
            }

            yield Feature(**properties)
