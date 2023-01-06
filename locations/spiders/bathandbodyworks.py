import hashlib

import scrapy

from locations.items import Feature


class BathAndBodyWorksSpider(scrapy.Spider):
    name = "bathandbodyworks"
    item_attributes = {"brand": "Bath & Body Works", "brand_wikidata": "Q810773"}
    allowed_domains = ["bathandbodyworks.com"]
    start_urls = ["https://bathandbodyworks.com/global-locations/global-locations.html"]

    def parse(self, response, **kwargs):
        for country in response.xpath('//a[contains(@class, "country-label")]'):
            country_url = country.xpath("@href").extract_first()
            country_name = country.xpath("text()").extract_first()
            yield scrapy.Request(
                country_url,
                callback=self.parse_global_country,
                meta={"country_name": country_name},
            )

    def parse_global_country(self, response):
        stores = response.xpath('//div[@class="store-location"]')
        for store in stores:
            properties = {}
            country_name = response.meta.get("country_name")
            name = store.xpath('.//p[@class="store-name"]/text()').extract_first()
            citystate = store.xpath('.//p[@class="location"]/text()').extract_first()
            location = store.xpath('string(.//p[text()="Location"]/following-sibling::p)').extract_first()
            phone = store.xpath('.//p[text()="Phone Number"]/following-sibling::p/text()').extract_first()

            properties["country"] = country_name
            if name:
                properties["name"] = name
            if citystate:
                if ", " in citystate:
                    city, state = citystate.split(", ")
                    properties["city"] = city
                else:
                    state = citystate

                if country_name not in state.title():
                    properties["state"] = state

            if location:
                properties["addr_full"] = location
            if phone and ("TBD" not in phone):
                properties["phone"] = phone

            # We aren't given a ref for these, so generate one based on a few
            # of the available properties that are likely to be unique.
            ref_input = ""
            for key in ["name", "phone", "location"]:
                if key in properties:
                    try:
                        ref_input += properties[key].encode("utf-8")
                    except TypeError:
                        ref_input += properties[key]

            properties["ref"] = hashlib.md5(ref_input.encode("utf-8")).hexdigest()

            yield Feature(**properties)
