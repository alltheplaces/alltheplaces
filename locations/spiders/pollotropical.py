# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem

class QuickleesSpider(scrapy.Spider):
    name = "pollotropical"
    allowed_domains = ["https://www.pollotropical.com/"]
    item_attributes = {
        "brand": "Pollo Tropical",
        "brand_wikidata": "Q3395356",
        "country": "USA",
    }

    start_urls = (
        'https://www.pollotropical.com/locations',
    )

    def parse(self, response):

        store = response.xpath(
            "//div[@class='styles__StyledCardInfo-s1y7dfjk-3 fncRsG']/div/h3/a/text()").extract()
        address = response.xpath(
            "//div[@class='styles__StyledCardInfo-s1y7dfjk-3 fncRsG']/p/a/@aria-label").extract()
        addressnew = [i.replace("Address: ", "").replace(
            ", click to open map", "") for i in address]

        city = [i.split(",")[0] for i in addressnew]
        street_adr = [i.split(",")[1] for i in addressnew]
        postcodes = re.findall(r'3\d{4}', (" ").join(addressnew))

        phone_and_hours = response.xpath(
            "//div[@class='styles__StyledCardInfo-s1y7dfjk-3 fncRsG']/p/text()").extract()
        phones = [phone_and_hours[i] for i in range(0, len(phone_and_hours), 2)]
        
        sites = response.xpath("//div[@class='styles__StyledCardLinks-s1y7dfjk-4 eNbvts']/a/@href").extract()
        website = [sites[i] for i in range(0, len(sites), 2)]
        website.insert(16, 'https://www.pollotropical.com/locations')

        for index in range(len(store)):
            properties = {
                "name": store[index],
                "website": website[index],
                "addr_full": addressnew[index],
                "street_address": street_adr[index],
                "city": city[index],
                "state": "Florida",
                "postcode": postcodes[index],
                "country": "USA",
                "phone": phones[index]
            }
            yield GeojsonPointItem(**properties)
