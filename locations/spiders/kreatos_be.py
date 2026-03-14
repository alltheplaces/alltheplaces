from scrapy import Spider

from locations.items import Feature


class KreatosBESpider(Spider):
    name = "kreatos_be"
    item_attributes = {"brand": "Kreatos", "brand_wikidata": "Q113540702"}
    start_urls = ["https://www.kreatos.be/nl/maak-een-afspraak"]

    def parse(self, response):
        for location in response.xpath('//div[@typeof="Place"]'):
            if phone := location.xpath('.//a[contains(@href, "tel:")]/@href').get():
                phone = phone.replace("tel:", "")
            properties = {
                "ref": location.xpath("./@id").get(),
                "name": " ".join(filter(None, location.xpath('.//div[@class="title"]/a/text()').getall())).strip(),
                "lat": location.xpath("./@data-lat").get(),
                "lon": location.xpath("./@data-lng").get(),
                "addr_full": ", ".join(
                    filter(
                        None,
                        location.xpath('.//div[contains(@class, "field-address")]/div[@class="line"]/text()').getall(),
                    )
                ).strip(),
                "phone": phone,
                "website": "https://www.kreatos.be" + location.xpath('.//div[@class="title"]/a/@href').get(),
            }
            yield Feature(**properties)
