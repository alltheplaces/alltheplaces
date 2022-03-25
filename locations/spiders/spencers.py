# -*- coding: utf-8 -*-
import scrapy
import re


from locations.items import GeojsonPointItem


class Spencers(scrapy.Spider):

    name = "spencers"
    item_attributes = {"brand": "Spencer's"}
    download_delay = 0.2
    allowed_domains = ("spencersonline.com",)
    start_urls = ("https://www.spencersonline.com/custserv/locate_store.cmd",)

    def parse(self, response):
        store_list = response.xpath(
            './/div[@class="body_wrap "]/div/script[3]/text()'
        ).extract_first()
        store_properties = store_list.split("var store = new Object();")
        for store in store_properties:
            if "var allStores = [];" in store:
                continue
            else:
                ref = re.search(r"store.STORE_ID = '(.*?)';", str(store)).group(1)
                number = re.search(r"store.STORE_NUMBER = '(.*?)';", str(store)).group(
                    1
                )
                name = re.search(r"store.ADDRESS_LINE_1 = '(.*?)';", str(store)).group(
                    1
                )
                addr_full = re.search(
                    r"store.ADDRESS_LINE_2 = '(.*?)';", str(store)
                ).group(1)
                city = re.search(r"store.CITY = '(.*?)';", str(store)).group(1)
                state = re.search(r"store.STATE ='(.*?)';", str(store)).group(1)
                postcode = re.search(r"store.ZIP_CODE = '(.*?)';", str(store)).group(1)
                phone = re.search(r"store.PHONE = '(.*?)';", str(store)).group(1)
                country = re.search(r"store.COUNTRY_CODE ='(.*?)';", str(store)).group(
                    1
                )
                lat = re.search(r"store.LATITUDE = '(.*?)';", str(store)).group(1)
                lon = re.search(r"store.LONGITUDE = '(.*?)';", str(store)).group(1)

                properties = {
                    "ref": ref,
                    "name": name,
                    "addr_full": addr_full,
                    "city": city,
                    "state": state,
                    "postcode": postcode,
                    "phone": phone,
                    "country": country,
                    "lat": float(lat),
                    "lon": float(lon),
                    "website": response.url,
                    "extras": {"number": number},
                }
                yield GeojsonPointItem(**properties)
