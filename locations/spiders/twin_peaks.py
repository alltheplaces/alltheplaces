import scrapy

from locations.dict_parser import DictParser


class TwinPeaksSpider(scrapy.Spider):
    name = "twin_peaks"
    item_attributes = {
        "brand": "Twin Peaks",
        "brand_wikidata": "Q7858255",
    }
    start_urls = [
        "https://twinpeaksrestaurant.com/api/locations",
        "https://twinpeaksmexico.mx/api/locations",
    ]

    def parse(self, response):
        for row in response.json():
            item = DictParser.parse(row["acf"])
            item.update(
                {
                    "name": row["title"]["rendered"],
                    "state": (item["state"] or {}).get("value"),
                    "website": row["link"],
                }
            )
            yield item
