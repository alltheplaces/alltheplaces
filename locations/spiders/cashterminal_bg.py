from scrapy import Spider

from locations.items import Feature


class CashterminalBGSpider(Spider):
    name = "cashterminal_bg"
    item_attributes = {"brand": "Cashterminal", "brand_wikidata": "Q115668697"}
    allowed_domains = ["www.cashterminal.bg"]
    start_urls = ["https://www.cashterminal.bg/places"]
    no_refs = True
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = True

    def parse(self, response):
        for location in response.xpath("//li[@class='contact-link']/a[@data-lat]"):
            properties = {
                "name": location.xpath("./text()").get(),
                "lat": location.xpath("./@data-lat").get(),
                "lon": location.xpath("./@data-long").get(),
            }
            yield Feature(**properties)
