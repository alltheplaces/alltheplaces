import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class BucadiBeppoSpider(scrapy.Spider):
    name = "bucadibeppo"
    item_attributes = {"brand": "Buca di Beppo", "brand_wikidata": "Q4982340"}
    allowed_domains = ["bucadibeppo.com"]
    start_urls = ["https://locations.bucadibeppo.com/us"]

    def parse(self, response):
        urls = response.xpath(
            '//a[@class="c-directory-list-content-item-link"]/@href | //*[@class="Teaser-titleLink Link Link--primary"]/@href'
        ).extract()
        if urls and not response.xpath('//*[@class="c-nearby-locations-header"]').extract():
            for url in urls:
                yield scrapy.Request(response.urljoin(url), callback=self.parse)
        else:
            name = self.xpath_join(response.xpath('//*[@id="location-name" and @itemprop="name"]//text()').extract())
            address = response.xpath('//*[@itemprop="address"]')[0]
            street = clean_address(address.xpath('.//*[@itemprop="streetAddress"]//text()').getall())
            city = address.xpath('.//*[@itemprop="addressLocality"]/text()').extract_first()
            state = address.xpath('.//*[@itemprop="addressRegion"]/text()').extract_first()
            postalcode = address.xpath('.//*[@itemprop="postalCode"]/text()').extract_first()
            phone = address.xpath('//*[@itemprop="telephone"]/text()').extract_first()
            hours = response.xpath('//*[@class="Nap-addressHoursWrapper"]//@data-days').extract_first()
            latitude = response.xpath('//*[@itemprop="latitude"]/@content').extract_first()
            longitude = response.xpath('//*[@itemprop="longitude"]/@content').extract_first()
            reservation_url = response.xpath('//*[text()="Make a Reservation"]/@href').extract_first()
            ref = response.url.split("/")[-1]
            if reservation_url:
                ref = "".join(re.findall("store=([0-9]+)&", reservation_url))
            properties = {
                "name": name.strip(),
                "ref": ref,
                "street": street.strip(),
                "city": city.strip(),
                "postcode": postalcode.strip(),
                "state": state.strip(),
                "country": "US",
                "phone": phone.strip(),
                "website": response.url,
                "lat": float(latitude),
                "lon": float(longitude),
                "opening_hours": self.parse_hours(hours) if hours else None,
            }
            yield Feature(**properties)

    def xpath_join(self, values: list, sep=" ") -> str:
        return f"{sep}".join(filter(None, [value.strip() for value in values]))

    def parse_hours(self, store_hours):
        store_hours = json.loads(store_hours)
        opening_hours = OpeningHours()

        for weekday in store_hours:
            day = weekday.get("day").title()
            for interval in weekday["intervals"]:
                if isinstance(interval, dict):
                    open_time = str(interval.get("start"))
                    close_time = str(interval.get("end"))
                    opening_hours.add_range(
                        day=day[:2],
                        open_time=open_time.zfill(4),
                        close_time=close_time.zfill(4),
                        time_format="%H%M",
                    )
        return opening_hours.as_opening_hours()
