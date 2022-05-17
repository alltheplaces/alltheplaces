# -*- coding: utf-8 -*-

import scrapy
from locations.items import GeojsonPointItem


class JJillSpider(scrapy.Spider):
    name = "jjill"
    item_attributes = {"brand": "J.Jill", "brand_wikidata": "Q64448268"}
    allowed_domains = ["jjill.com"]
    start_urls = ["https://locations.jjill.com/"]

    def parse(self, response):
        urls = response.xpath('//*[@class="indexpage_node"]/a/@href').extract()
        if urls:
            for url in urls:
                yield scrapy.Request(response.urljoin(url), callback=self.parse)
        else:
            name = response.xpath('//*[@class="store-name"]/text()').extract_first()
            street = response.xpath(
                '//*[@itemprop="streetAddress"]//text()'
            ).extract_first()
            city = response.xpath(
                '//*[@itemprop="addressLocality"]/text()'
            ).extract_first()
            state = response.xpath(
                '//*[@itemprop="addressRegion"]/text()'
            ).extract_first()
            postalcode = response.xpath(
                '//*[@itemprop="postalCode"]/text()'
            ).extract_first()
            country = response.xpath(
                '//*[@itemprop="addressCountry"]/text()'
            ).extract_first()
            phone = response.xpath('//*[@itemprop="telephone"]/text()').extract_first()
            latitude = response.xpath(
                '//*[@property="place:location:latitude"]/@content'
            ).extract_first()
            longitude = response.xpath(
                '//*[@property="place:location:longitude"]/@content'
            ).extract_first()
            ref = response.url.strip("/").split("/")[-1]
            hours = response.xpath(
                '//h2[text()="Store Hours"]/following-sibling::div[@class="desktop"]/div[contains(@class, "day-hours")]'
            )
            properties = {
                "name": name.strip(),
                "ref": ref,
                "street": street.strip(),
                "city": city.strip(),
                "postcode": postalcode.strip(),
                "state": state.strip(),
                "country": country.strip(),
                "phone": phone.strip(),
                "website": response.url,
                "lat": float(latitude),
                "lon": float(longitude),
                "opening_hours": self.parse_hours(hours) if hours else None,
            }
            yield GeojsonPointItem(**properties)

    def parse_hours(self, store_hours):
        opening_hours = []

        for day_hour in store_hours:
            day = (
                day_hour.xpath('.//*[@class="day"]/text()')
                .extract_first()
                .strip(" :")
                .title()
            )
            hrs = day_hour.xpath('.//*[@class="hr"]/text()').extract_first()
            if "closed" in hrs.lower():
                continue
            opening_hours.append(f"{day[:2]} {hrs}")

        return "; ".join(opening_hours)
