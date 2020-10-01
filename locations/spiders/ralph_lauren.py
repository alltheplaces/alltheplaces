# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem

class LanghamHotel(scrapy.Spider):
    name = "langham"
    allowed_domains = ["www.langhamhotels.com","www.cordishotels.com", "www.langhamresidences.com"]
    start_urls = (
        'https://www.langhamhotels.com/en/locations/',
    )

    def parse(self, response):
        #gather URLs of all Langham Hotel locations
        all_locations = response.xpath('//div[@class="listing-item locations-item"]/a/@href').extract()

        for locations in all_locations:
            yield scrapy.Request(response.urljoin(locations),callback=self.parse_locations)

    def parse_locations(self,response):
        data = response.xpath('//script[@type="application/ld+json"]/text()').extract_first()

        if data and self.isValidJson(data):
            try:
                data = json.loads(data)

                # preparation to extract data in the next step, return empty if there is no geo/address in the json
                # otherwise throws error while setting properties
                geo_data = data.get("geo", {})
                address_data = data.get("address", {})

                # all properties set with data.get to set proper value or None if empty/non-existent
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

        else:
            # some of the websites don't provide location information with application/ld+json
            # or return invalid JSON
            # the only other option is to crawl the footers in that case, which seems messy to me
            pass

    def isValidJson(self,jsondata):
        try:
            json.loads(jsondata)
        except Exception as e:
            return False
        return True
