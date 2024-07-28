import json

import scrapy

from locations.items import Feature


class LanghamHotelsSpider(scrapy.Spider):
    name = "langham_hotels"
    allowed_domains = [
        "www.langhamhotels.com",
        "www.cordishotels.com",
        "www.langhamresidences.com",
    ]
    start_urls = ("https://www.langhamhotels.com/en/locations/",)

    def parse(self, response):
        # gather URLs of all Langham Hotel locations
        all_locations = response.xpath('//div[@class="listing-item locations-item"]/a/@href').extract()

        for locations in all_locations:
            yield scrapy.Request(response.urljoin(locations), callback=self.parse_locations)

    def parse_locations(self, response):
        data = response.xpath('//script[@type="application/ld+json"]/text()').extract_first()

        if data:
            try:
                data = json.loads(data)

                # preparation to extract data in the next step, return empty if there is no geo/address in the json
                # otherwise it throws error while setting properties (since no geo/address in json)
                geo_data = data.get("geo", {})
                address_data = data.get("address", {})

                # all properties set with data.get to set proper value or None if empty/non-existent
                properties = {
                    "ref": response.url,
                    "name": data.get("name", None),
                    "lat": geo_data.get("latitude", None),
                    "lon": geo_data.get("longitude", None),
                    "phone": data.get("telephone", None),
                    "addr_full": address_data.get("streetAddress", None),
                    "country": address_data.get("addressCountry", None),
                    "postcode": address_data.get("postalCode", None),
                }

                yield Feature(**properties)

            except Exception as e:
                self.logger.warn("----------------- Error -----------------: {}".format(e))

        else:
            # some of the websites don't provide location information with application/ld+json
            # or return invalid JSON
            # the footers provide some location information,
            # but there is no common pattern for these remaining 8 hotels to extract the locations nicely
            # https://www.langhamhotels.com/en/langham-place/changsha/
            # https://www.langhamhotels.com/en/the-langham/boston/
            # https://www.langhamhotels.com/en/langham-place/xiamen/
            # https://www.langhamhotels.com/en/langham-place/ningbo/
            # https://www.langhamhotels.com/en/langham-place/haining/
            # https://www.langhamhotels.com/en/langham-place/guangzhou/
            # https://www.langhamhotels.com/en/the-langham/haikou/
            # https://www.langhamresidences.com/en/the-langham/nymphenburg/ (no location information)
            pass
