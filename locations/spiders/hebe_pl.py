import scrapy

from locations.items import Feature


class HebePLSpider(scrapy.Spider):
    name = "hebe_pl"
    item_attributes = {"brand": "Hebe", "brand_wikidata": "Q113093841"}
    start_urls = ["https://www.hebe.pl/sklepy"]

    def parse(self, response, **kwargs):
        for shop in response.xpath("//*[@data-lat]"):
            item = Feature()
            item["name"] = shop.xpath('.//*[@class="store-popup__name text--uppercase"]/text()').get()
            item["street_address"] = shop.xpath('.//*[@class="store-popup__address"]/text()').get()
            item["ref"] = shop.xpath("./@data-id").get()
            item["lat"] = shop.xpath("./@data-lat").get()
            item["lon"] = shop.xpath("./@data-lng").get()
            item["website"] = response.urljoin(shop.xpath('.//a[@title="Informacje o sklepie"]/@href').get())
            city_postal = shop.xpath('.//*[@class="store-popup__city"]/text()').get(default="").split(",")
            if len(city_postal) == 2:
                item["city"] = city_postal[0].strip()
                item["postcode"] = city_postal[1].strip()
            yield item
