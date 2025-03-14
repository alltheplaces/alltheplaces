import re

import scrapy

from locations.items import Feature


class FraserHealthSpider(scrapy.Spider):
    name = "fraser_health"
    item_attributes = {"operator": "Fraser Health Authority", "operator_wikidata": "Q5493608"}
    allowed_domains = ["fraserhealth.ca"]
    start_urls = [
        "https://www.fraserhealth.ca//sxa/search/results/?s={EEFB374B-EF65-4B44-B06E-AF16ECE464AA}&sig=location&o=Title,Ascending&p=500&v={36068498-7115-494B-8659-DFFB2B83EBF5}&site=null",
    ]

    def parse_place(self, response):
        coords = response.xpath('//*[@class="component map-static-content o-grid__col"]/div/a/@href').extract_first()
        lat = re.search(r"q=(.*?),", coords).groups()[0]
        lng = re.search(r",(.*)$", coords).groups()[0]
        state = response.xpath('//*[@class="location-province field-province"]/text()').extract_first()
        if state is not None:
            state = state.replace(".", "")
            state = state.strip()

        properties = {
            "ref": response.meta["ref"],
            "name": response.xpath('//*[@class="title field-title field-title"]/a/@title').extract_first(),
            "street_address": response.xpath('//*[@class="field-address"]/text()').extract_first(),
            "city": response.xpath('//*[@class="field-title"]/a/@title').extract_first(),
            "state": state,
            "postcode": response.xpath('//*[@class="postal-code field-postalcode"]/text()').extract_first(),
            "country": "CA",
            "lat": lat,
            "lon": lng,
            "phone": response.xpath('//*[@class="phone field-phone"]/text()').extract_first(),
            "website": response.url,
        }

        yield Feature(**properties)

    def parse(self, response):
        places = response.json()

        for place in places["Results"]:
            yield scrapy.Request(url=place["Url"], callback=self.parse_place, meta={"ref": place["Id"]})
