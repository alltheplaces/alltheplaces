# -*- coding: utf-8 -*-
import scrapy
import re
import json
from locations.items import GeojsonPointItem


states = [
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DC",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
]


class BelkSpider(scrapy.Spider):
    name = "belk"
    item_attributes = {"brand": "Belk"}
    allowed_domains = ["www.belk.com"]
    start_urls = ("https://www.belk.com/stores-near-you/",)
    download_delay = 0.2

    def start_requests(self):
        url = "https://www.belk.com/stores-near-you/"

        for state in states:
            headers = {
                "origin": "https://www.belk.com",
                "Referer": "https://www.belk.com/stores/?showForm=true",
            }

            formdata = {
                "dwfrm_storelocator_state": "{}".format(state),
                "dwfrm_storelocator_findbystate": "Search",
            }

            yield scrapy.http.FormRequest(
                url, self.parse, method="POST", headers=headers, formdata=formdata
            )

    def parse(self, response):
        store_urls = response.xpath('//a[@class="store-details-link"]/@href').extract()
        for store_url in store_urls:
            yield scrapy.Request(response.urljoin(store_url), callback=self.parse_store)

    def parse_store(self, response):
        store_data = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).extract_first()
        data_obj = json.loads(store_data)
        ref = re.search(r".+/?StoreID=(.+)", response.url).group(1)
        street = data_obj.get("address").get("streetAddress")
        city = data_obj.get("address").get("addressLocality")
        state = data_obj.get("address").get("addressRegion")
        postcode = data_obj.get("address").get("postalCode")
        lat = data_obj.get("geo").get("latitude")
        lon = data_obj.get("geo").get("longitude")
        phone = data_obj.get("telephone")
        name = data_obj.get("name")
        country = data_obj.get("address").get("addressCountry")

        properties = {
            "ref": ref,
            "addr_full": street,
            "city": city,
            "state": state,
            "postcode": postcode,
            "lat": lat,
            "lon": lon,
            "phone": phone,
            "name": name,
            "country": country,
            "website": response.request.url,
        }

        yield GeojsonPointItem(**properties)
