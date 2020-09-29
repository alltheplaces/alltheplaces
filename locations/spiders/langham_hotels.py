# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem

class LanghamHotel(scrapy.Spider):
    name = "langham_all"
    allowed_domains = ["www.langhamhotels.com","www.cordishotels.com", "www.langhamresidences.com"]
    start_urls = (
        'https://www.langhamhotels.com/en/locations/',
    )

    def parse_footer(self,response):
        pass

    def parse_locations(self,response):
        data = response.xpath('//script[@type="application/ld+json"]/text()').extract_first()

        if data:
            try:
                data = json.loads(data)

                geo_data = data.get("geo", {})
                address_data = data.get("address", {})

                properties = {
                    'ref': response.url,
                    'name': data.get("name", None),
                    'lat': geo_data.get("latitude", None),
                    'lon': geo_data.get("longitude", None),
                    'phone': data.get("telephone", None),
                    'addr_full': address_data.get("streetAddress", None),
                    'country': address_data.get("addressCountry", None),
                    'postcode': address_data.get("postalCode", None),
                }

                yield GeojsonPointItem(**properties)

            except Exception as e:
                self.logger.warn("----------------- Error -----------------: {}".format(e))
                self.logger.warn("------------------ URL ------------------: {}".format(response.url))
        else:
            self.parse_footer(response)

    def parse(self, response):
        all_locations = response.xpath('//div[@class="listing-item locations-item"]/a/@href').extract()

        for locations in all_locations:
            yield scrapy.Request(response.urljoin(locations),callback=self.parse_locations)