from scrapy import Spider

from locations.items import Feature


class CashterminalBGSpider(Spider):
    name = "cashterminal_bg"
    item_attributes = {"brand": "Cashterminal", "brand_wikidata": "Q115668697"}
    allowed_domains = ["www.cashterminal.eu"]
    start_urls = ["https://www.cashterminal.eu/places"]
    no_refs = True

    def parse(self, response):
        for location in response.xpath("//div[@class='markerList']/a[@data-lat]"):
            properties = {
                "name": location.get(),
                "lat": location.xpath("./@data-lat"),
                "lon": location.xpath("./@data-long"),
            }
            yield Feature(**properties)
