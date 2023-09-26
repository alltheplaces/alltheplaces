import base64
import json

import scrapy

from locations.items import Feature


class RalphLaurenSpider(scrapy.Spider):
    name = "ralph_lauren"
    allowed_domains = ["www.ralphlauren.com"]
    start_urls = ("https://www.ralphlauren.com/Stores-ShowCountries",)

    def parse(self, response):
        # gather URLs of all countries
        countries = response.xpath('//a[@class="store-directory-countrylink"]/@href').extract()

        for country in countries:
            # build URL for per country overview of all stores, countrycode is after the equals sign, e.g. /Stores-ShowStates?countryCode=US
            url = (
                "/findstores?dwfrm_storelocator_country="
                + (country.split("=", 1)[1])
                + "&dwfrm_storelocator_findbycountry=Search&findByValue=CountrySearch"
            )
            yield scrapy.Request(response.urljoin(url), callback=self.parse_city)

    def parse_city(self, response):
        # get all stores per country
        stores = response.xpath('//span[@class="store-listing-name"]/a/@href').extract()

        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_locations)

    def parse_locations(self, response):
        # get json which provides most of the data
        data = response.xpath('//div[@class="storeJSON hide"]/@data-storejson').extract_first()

        # opening hours are not in json, thus need to be scraped separately
        hours = response.xpath('//tr[@class="store-hourrow"]//td//text()').getall()
        opening_hours = []

        for i in hours:
            opening_hours.append(i.strip())

        # some stores have a second address line which is not in the json
        store_address = response.xpath('//p[@class="store-address"]/text()').extract()

        if len(store_address) == 6:
            address = store_address[0].strip()
        else:
            address = "\n".join([store_address[0].strip(), store_address[1].strip()])

        if data:
            data = json.loads(data)[0]

            # decode base64 string
            name = data.get("name", None)
            name = base64.b64decode(name).decode("utf-8")

            properties = {
                "ref": data.get("id", None),
                "name": name,
                "lat": data.get("latitude", None),
                "lon": data.get("longitude", None),
                "phone": data.get("phone", None),
                "addr_full": address,
                "state": data.get("stateCode", None),
                "city": data.get("city", None),
                "country": data.get("countryCode", None),
                "postcode": data.get("postalCode", None),
                "opening_hours": opening_hours,
            }

            yield Feature(**properties)
