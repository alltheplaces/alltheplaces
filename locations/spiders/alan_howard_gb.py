from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class AlanHowardGBSpider(Spider):
    name = "alan_howard_gb"
    item_attributes = {"brand": "Alan Howard", "brand_wikidata": "Q119260364"}
    allowed_domains = ["www.alanhoward.co.uk"]
    start_urls = ["https://www.alanhoward.co.uk/store-locator/"]

    def parse(self, response):
        for location in response.xpath('//div[contains(@class, "store-card-wrapper")]/div'):
            properties = {
                "ref": location.xpath(".//@id").get().replace("store-", ""),
                "name": location.xpath('.//p[@class="store-heading"]/text()').get(),
                "addr_full": ", ".join(
                    filter(None, location.xpath('.//div[@class="more-details-address"]//text()').getall()[:-1])
                ),
                "phone": location.xpath('.//div[@class="more-details-address"]/p[last()]/text()').get(),
                "lat": location.xpath(".//@data-lat").get(),
                "lon": location.xpath(".//@data-lng").get(),
            }
            properties["website"] = "https://www.alanhoward.co.uk/our-stores/?store=" + properties["ref"]
            apply_category(Categories.SHOP_HAIRDRESSER_SUPPLY, properties)
            yield Feature(**properties)
