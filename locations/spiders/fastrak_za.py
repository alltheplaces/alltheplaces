import scrapy

from locations.google_url import url_to_coords
from locations.items import Feature


class FastrakZASpider(scrapy.Spider):
    name = "fastrak_za"
    start_urls = ["https://www.fastrak.co.za/pages/fastrak-stores"]
    item_attributes = {
        "brand": "Fastrak",
        "brand_wikidata": "Q120799603",
    }
    no_refs = True

    def parse(self, response):
        for location in response.xpath('.//tr[@data-mce-fragment="1"]')[1:]:
            item = Feature()
            item["state"] = location.xpath(".//td[1]/text()").get()
            item["branch"] = location.xpath(".//td[2]/text()").get().replace("Fastrak: ", "")
            item["phone"] = location.xpath(".//td[3]/text()").get()
            item["email"] = location.xpath(".//td[4]/a/@href").get()
            item["lat"], item["lon"] = url_to_coords(location.xpath(".//td[5]/a/@href").get())

            yield item
