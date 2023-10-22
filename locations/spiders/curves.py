import re

import scrapy

from locations.items import Feature


class CurvesSpider(scrapy.Spider):
    name = "curves"
    item_attributes = {"brand": "Curves"}
    allowed_domains = ["curves.com"]
    start_urls = ("https://www.curves.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath("//url/loc/text()").extract()
        regex = re.compile(r"https://www.curves.com/locations/\S+")
        for path in city_urls:
            if re.search(regex, path):
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )
            else:
                pass

    def parse_store(self, response):
        if response.xpath(
            '//div[@class="field field-name-field-franchise-club-hours field-type-text-long field-label-hidden"]/div/div'
        ).extract_first():
            store_hours_html = str(
                response.xpath(
                    '//div[@class="field field-name-field-franchise-club-hours field-type-text-long field-label-hidden"]/div/div'
                ).extract_first()
            )
            p = re.compile(r"<.*?>")
            store_hours = p.sub(" ", store_hours_html)
            # storeHours = storeHours.replace('\\n', ' - ')
            store_hours = store_hours.strip()
        else:
            store_hours = response.xpath(
                '//div[@class="field field-name-field-franchise-club-hours field-type-text-long field-label-hidden"]/div/div'
            ).extract_first()

        properties = {
            "name": response.xpath("//h1/text()").extract_first(),
            "ref": response.xpath("//h1/text()").extract_first(),
            "addr_full": response.xpath('//div[@class="thoroughfare"]/text()').extract_first(),
            "city": response.xpath('//div[@class]/span[@class="locality"]/text()').extract_first(),
            "state": response.xpath('//div[@class]/span[@class="state"]/text()').extract_first(),
            "postcode": response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
            "country": response.xpath('//span[@class="country"]/text()').extract_first(),
            "phone": response.xpath(
                '//div[@class="field field-name-field-franchise-phone field-type-telephone field-label-hidden"]/div/div[@class="field-item even"]/text()'
            ).extract_first(),
            "website": response.request.url,
            "opening_hours": store_hours,
            # 'lon': float(response.xpath('//head/script[9]').extract_first().split('"coordinates":[')[1].split(']')[0].split(',')[0]),
            # 'lat': float(response.xpath('//head/script[9]').extract_first().split('"coordinates":[')[1].split(']')[0].split(',')[1]),
        }

        yield Feature(**properties)
