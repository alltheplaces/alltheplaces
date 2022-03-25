# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import re


class TemplateSpider(scrapy.Spider):
    name = "casino"
    item_attributes = {"brand": "Casino"}
    allowed_domains = ["magasins.supercasino.fr"]
    start_urls = ("https://magasins.supercasino.fr/fr",)

    def parse(self, response):
        shopList = response.xpath('//div[@id="List_Store"]//li[@class="ItemMagasin"]')

        for shop in shopList:
            shopPage = shop.xpath('.//span[@class="MoreInfos"]/../@href').get()
            yield scrapy.Request(shopPage, callback=self.parse_shop)

    def parse_shop(self, response):
        ref = re.search(r"\/([^\/]+)$", response.url).group(1)

        name = response.xpath('.//span[@class="Brand"]/text()').get()

        telephone = response.xpath(
            './/div[@class="StoreInformations"]//a[@itemprop="telephone"]/text()'
        ).get()
        openingHours = response.xpath(
            './/div[@class="StoreInformations"]//meta[@itemprop="openingHours"]/@content'
        ).get()

        city = response.xpath('.//span[@class="City"]/text()').get()
        postalCode = response.xpath(
            './/div[@class="StoreInformations"]//span[@itemprop="postalCode"]/text()'
        ).get()
        postalCode = response.xpath(
            './/div[@class="StoreInformations"]//span[@itemprop="postalCode"]/text()'
        ).get()
        streetAddress = (
            response.xpath(
                './/div[@class="StoreInformations"]//span[@itemprop="streetAddress"]/text()'
            )
            .get()
            .replace("\n", "")
            .replace("\r", "")
            .strip()
        )

        streetExtracts = re.search(
            r"^(?:(\d+ ?(?:[a-z]|bis|ter)?)(?: ?[-/]? ?(\d+ ?(?:[a-z]|bis|ter)?))? +)?(.+)$",
            streetAddress,
            re.IGNORECASE,
        )
        roadNum = streetExtracts.group(1)
        secondRoadNum = streetExtracts.group(2)
        street = streetExtracts.group(3)

        properties = {
            "ref": ref,
            "name": name,
            "phone": telephone,
            "city": city,
            "postcode": postalCode,
            "housenumber": roadNum,
            "street": street,
            "addr_full": streetAddress,
            "website": response.url,
            "opening_hours": openingHours,
            "extras": {"addr_2_housenumber": secondRoadNum},
        }

        yield GeojsonPointItem(**properties)
