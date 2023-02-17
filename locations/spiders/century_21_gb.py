import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.spiders.century_21 import Century21Spider


class Century21GBSpider(scrapy.Spider):
    name = "century_21_gb"
    item_attributes = Century21Spider.item_attributes
    allowed_domains = ["century21uk.com"]
    start_urls = ["https://www.century21uk.com/find-an-agent/"]

    def parse(self, response):
        agents = response.xpath('//div[@id="agent-results"]//h4/a/@href').extract()
        for agent in agents:
            yield scrapy.Request(url=agent, callback=self.agent_parse)

    def agent_parse(self, response):
        data = response.xpath('//script[@type="application/ld+json"]//text()').get()
        if data:
            data_json = json.loads(data)
            item = LinkedDataParser.parse_ld(data_json)
            item["ref"] = data_json.get("name")

            yield item

        else:
            address = response.xpath('normalize-space(//ul[@class="contact-details"]/li/text())').get()
            if address != "":
                postcode = re.findall("[0-9]{5}|[A-Z0-9]{3} [A-Z0-9]{3}", address)[0]
                phone = response.xpath('normalize-space(//ul[@class="contact-details"]/li/a/text())').get()
                email = response.xpath('//ul[@class="contact-details"]//a[contains(@href, "mailto")]/@href').get()
                name = response.xpath('//div[@id="banner"]//h1/text()').get()
                days = response.xpath('//ul[@class="opening-hours"]/li')
                oh = OpeningHours()
                for day in days:
                    if day.xpath("./text()")[1].get().replace("\t", "").replace("\n", "").strip() == "CLOSED":
                        continue
                    oh.add_range(
                        day=day.xpath("./span/text()").get().strip().split(" - ")[0][:3],
                        open_time=day.xpath("./text()")[1]
                        .get()
                        .replace("\t", "")
                        .replace("\n", "")
                        .split(" - ")[0]
                        .strip(),
                        close_time=day.xpath("./text()")[1]
                        .get()
                        .replace("\t", "")
                        .replace("\n", "")
                        .split(" - ")[1]
                        .strip(),
                    )
                properties = {
                    "name": name,
                    "ref": name,
                    "addr_full": address,
                    "postcode": postcode,
                    "phone": phone,
                    "email": email,
                    "website": response.url,
                    "opening_hours": oh.as_opening_hours(),
                }

                yield Feature(**properties)
