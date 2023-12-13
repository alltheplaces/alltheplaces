import json
import re

import scrapy

from locations.items import Feature


class CatherinesSpider(scrapy.Spider):
    name = "catherines"
    item_attributes = {"brand": "Catherine's", "brand_wikidata": "Q64026208"}
    allowed_domains = ["stores.catherines.com"]
    download_delay = 0.5
    start_urls = ("https://stores.catherines.com/",)

    def parse_stores(self, response):
        data = response.xpath('normalize-space(//script[@type="application/ld+json"]/text())').extract_first()
        ref = re.findall(r"[^(\/)]+$", response.url)
        if len(ref) > 0:
            ref = ref[0].split(".")[0]
        try:
            json_data = json.loads(data)
            properties = {
                "addr_full": json_data[0]["address"]["streetAddress"],
                "phone": json_data[0]["telephone"],
                "city": json_data[0]["address"]["addressLocality"],
                "state": json_data[0]["address"]["addressRegion"],
                "postcode": json_data[0]["address"]["postalCode"],
                "ref": ref,
                "website": response.url,
                "lat": json_data[0]["geo"]["latitude"],
                "lon": json_data[0]["geo"]["longitude"],
            }
            properties["opening_hours"] = (json_data[0]["openingHours"],)
            yield Feature(**properties)
        except ValueError:
            return

    def parse_city_stores(self, response):
        stores = response.xpath('//div[@id="rls_maplist"]/div/ul/div/li/div/a/@href').extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse_state(self, response):
        city_urls = response.xpath('//div[@id="rls_maplist"]/div/ul/div/li/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)

    def parse(self, response):
        urls = response.xpath('//div[@id="rls_maplist_domain"]/div/ul/div/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
