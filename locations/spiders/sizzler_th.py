import scrapy

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class SizzlerTHSpider(scrapy.Spider):
    name = "sizzler_th"
    item_attributes = {
        "brand": "Sizzler",
        "brand_wikidata": "Q1848822",
    }
    start_urls = ["https://www.sizzler.co.th/en/all-branches"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response):
        data_addr = response.xpath('//div[@class="col-lg-7"]/h2/text()')
        data_phone = response.xpath('//div[@class="col-lg-5"]/h2/text()')
        for addr, phone in zip(data_addr, data_phone):
            properties = {
                "name": "Sizzler",
                "addr_full": addr.get(),
                "phone": phone.get(),
                "ref": f"Sizzler-{addr}",
            }
            yield Feature(**properties)
