import re

import scrapy

from locations.items import Feature


class CbreSpider(scrapy.Spider):
    name = "cbre"
    item_attributes = {"brand": "CBRE", "brand_wikidata": "Q1023013"}
    allowed_domains = ["cbre.us"]
    start_urls = ("https://www.cbre.us/people-and-offices",)

    def parse(self, response):
        urls = response.xpath('//li[@class="list-item list-item--second-level"]//a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        store_js = response.xpath('//div[@class="OfficeMapsWrapper google-map"]//script//text()').extract()
        if store_js:
            store = store_js[0]
            storere = re.findall(r'\(("[^)]+")', store)
            for item in storere:
                item = item.replace("\\", "")
                item = item.replace('"', "")
                properties = {
                    "ref": item.split(",")[-4].split("   ")[0] + "-" + item.split(",")[0],
                    "name": item.split(",")[0],
                    "addr_full": item.split(",")[-4].split("   ")[0],
                    "state": item.split(", ")[-3].split(" ")[0],
                    "city": item.split(",")[-4].split("   ")[-1],
                    "postcode": item.split(", ")[-3].split(" ")[1],
                    "country": "US",
                    "phone": response.xpath(
                        '//div[@class="numbers-wrapper__numbers numbers-wrapper__numbers--office tel"]//text()'
                    )
                    .extract_first()
                    .replace("+", ""),
                    "lat": float(item.split(",")[-2].replace('"', "")),
                    "lon": float(item.split(",")[-1].replace('"', "")),
                }

                yield Feature(**properties)
            else:
                pass
