# -*- coding: utf-8 -*-
import json
import logging
import re

import scrapy

from locations.items import GeojsonPointItem

URL = "https://data.discounttire.com/webapi/discounttire.graph"


class DiscountTireSpider(scrapy.Spider):
    name = "discount_tire"
    item_attributes = {"brand": "Discount Tire", "brand_wikidata": "Q5281735"}
    allowed_domains = ["discounttire.com"]
    start_urls = [
        "https://www.discounttire.com/sitemap.xml",
    ]
    download_delay = 3.0
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
    }

    def parse(self, response):
        response.selector.remove_namespaces()
        url = response.xpath(
            '//loc[contains(text(), "Sitemap-Categories")]/text()'
        ).extract_first()

        yield scrapy.Request(url=url, callback=self.parse_site)

    def parse_site(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath('//loc[contains(text(), "/store/")]/text()').extract()

        for url in urls:
            store_code = re.search(r".+/(.+?)/?(?:\.html|$)", url).group(1)
            payload = {
                "operationName": "StoreByCode",
                "variables": {"storeCode": f"{store_code}"},
                "query": "query StoreByCode($storeCode: String!) {\n  store {\n    byCode(storeCode: $storeCode) {\n      ...myStoreFields\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment myStoreFields on StoreData {\n  code\n  address {\n    country {\n      isocode\n      name\n      __typename\n    }\n    email\n    line1\n    line2\n    phone\n    postalCode\n    region {\n      isocodeShort\n      name\n      __typename\n    }\n    town\n    __typename\n  }\n  winterStore\n  baseStore\n  description\n  displayName\n  isBopisTurnedOff: bopisTurnedOff\n  distance\n  legacyStoreCode\n  geoPoint {\n    latitude\n    longitude\n    __typename\n  }\n  rating {\n    rating\n    numberOfReviews\n    __typename\n  }\n  weekDays {\n    closed\n    formattedDate\n    dayOfWeek\n    __typename\n  }\n  __typename\n}\n",
            }

            yield scrapy.Request(
                url=URL,
                method="POST",
                body=json.dumps(payload),
                callback=self.parse_stores,
                meta={"website": url},
            )

    def parse_stores(self, response):
        store_data = json.loads(response.text)
        data = store_data["data"]["store"]["byCode"]

        if data:
            properties = {
                "name": data["displayName"],
                "ref": data["code"],
                "addr_full": data["address"]["line1"],
                "city": data["address"]["town"],
                "state": data["address"]["region"]["isocodeShort"],
                "postcode": data["address"]["postalCode"],
                "country": data["address"]["country"]["isocode"],
                "phone": data["address"].get("phone"),
                "website": response.meta.get("website"),
                "lat": float(data["geoPoint"]["latitude"]),
                "lon": float(data["geoPoint"]["longitude"]),
            }

            yield GeojsonPointItem(**properties)
