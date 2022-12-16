import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class Century21UkSpider(scrapy.Spider):
    name = "century_21_uk"
    item_attributes = {
        "brand": "Century21",
        "brand_wikidata": "Q1054480",
    }
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
            oh = OpeningHours()
            openingHours = (
                [data_json.get("openingHoursSpecification")]
                if isinstance(data_json.get("openingHoursSpecification"), dict)
                else data_json.get("openingHoursSpecification")
            )
            for item in openingHours:
                days = (
                    [item.get("dayOfWeek")]
                    if isinstance(item.get("dayOfWeek"), str)
                    else item.get("dayOfWeek")
                )
                for day in days:
                    oh.add_range(
                        day=day,
                        open_time=item.get("opens"),
                        close_time=item.get("closes"),
                    )
            addr_full = data_json.get("address", {}).get("address_line_1")
            if not addr_full:
                addr_full = data_json.get("address", {}).get("streetAddress")
            properties = {
                "name": data_json.get("name"),
                "ref": data_json.get("name"),
                "city": data_json.get("address", {}).get("addressLocality"),
                "addr_full": addr_full,
                "postcode": data_json.get("address", {}).get("postalCode"),
                "country": data_json.get("address", {}).get("addressCountry"),
                "lon": data_json.get("geo", {}).get("longitude"),
                "lat": data_json.get("geo", {}).get("latitude"),
                "phone": data_json.get("telephone"),
                "website": data_json.get("url"),
                "opening_hours": oh.as_opening_hours(),
            }

            yield GeojsonPointItem(**properties)
            
        else:
            address = response.xpath('normalize-space(//ul[@class="contact-details"]/li/text())').get()
            if address != '':
                postcode = re.findall("[0-9]{5}|[A-Z0-9]{3} [A-Z0-9]{3}", address)[0]
                phone = response.xpath('normalize-space(//ul[@class="contact-details"]/li/a/text())').get()
                email = response.xpath('//ul[@class="contact-details"]//a[contains(@href, "mailto")]/@href').get()
                name = response.xpath('//div[@id="banner"]//h1/text()').get()
                days = response.xpath('//ul[@class="opening-hours"]/li')
                oh = OpeningHours()
                for day in days:
                    if day.xpath('./text()')[1].get().replace('\t', '').replace('\n', '').strip() == 'CLOSED':
                        continue
                    oh.add_range(
                        day=day.xpath('./span/text()').get().strip().split(" - ")[0][:3],
                        open_time=day.xpath('./text()')[1].get().replace('\t', '').replace('\n', '').split(" - ")[0].strip(),
                        close_time=day.xpath('./text()')[1].get().replace('\t', '').replace('\n', '').split(" - ")[1].strip(),
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

                yield GeojsonPointItem(**properties)