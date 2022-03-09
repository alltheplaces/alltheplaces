# -*- coding: utf-8 -*-
import json
import re
import zlib

import scrapy

from scrapy import Selector
from locations.items import GeojsonPointItem
from urllib.parse import urlencode


class SearsSpider(scrapy.Spider):
    name = "sears"
    item_attributes = {"brand": "Sears"}
    allowed_domains = [
        "www.sears.com",
        "www.searsoutlet.com",
        "www.searshometownstores.com",
    ]
    download_delay = 0.3

    def start_requests(self):
        sears_url = "https://www.sears.com/Sitemap_Local.xml.gz"
        sears_outlet_url = "https://www.searsoutlet.com/sitemap.xml"
        sears_hts_url = "http://www.searshometownstores.com/sitemap-store-urls.xml"

        yield scrapy.Request(sears_url, callback=self.parse_sears)
        yield scrapy.Request(sears_outlet_url, callback=self.parse_sears_outlet)
        yield scrapy.Request(sears_hts_url, callback=self.parse_sears_hts)

    def parse_sears(self, response):
        decompressed_xml = zlib.decompress(response.body, 16 + zlib.MAX_WBITS)
        sel = Selector(text=decompressed_xml)
        for url in sel.xpath("//loc/text()").extract():
            if url.count("/") == 6:
                yield scrapy.Request(url.strip(), callback=self.parse_sears_store)

    def parse_sears_outlet(self, response):
        response.selector.remove_namespaces()
        base_url = "https://www.searsoutlet.com/br/api/store/"
        for url in response.xpath("//loc/text()").extract():
            if "br/store/" in url:
                store_name = re.search(r".+/(.+?)/?(?:\.html|$)", url.strip()).group(1)
                api_url = base_url + store_name
                yield scrapy.Request(api_url, callback=self.parse_sears_outlet_store)

    def parse_sears_hts(self, response):
        response.selector.remove_namespaces()
        base_url = (
            "http://www.searshometownstores.com/hometown/services/Store.Service.ss?"
        )
        for url in response.xpath("//loc/text()").extract():
            store_name = re.search(r".+/(.+?)/?(?:\.html|$)", url).group(1)
            params = {
                "format": "HTS",
                "name": store_name,
                "storehome": "T",
                "storekioskhome": "F",
            }
            yield scrapy.http.Request(
                base_url + urlencode(params), callback=self.parse_sears_hts_store
            )

    def parse_sears_store(self, response):
        # Handle redirects to closed store page, majority are regular store detail pages
        if response.request.meta.get("redirect_urls"):
            if "store-closed" in response.url:
                pass
        else:
            store_script_data = response.xpath(
                '//script[contains(text(),"var storeTitle")]/text()'
            ).extract_first()
            lat = re.search(r"lat = ([0-9.]*),", store_script_data).group(1)
            lon = re.search(r"lon = ([0-9.-]*),", store_script_data).group(1)
            ref = re.search(r'unitNumber = "([0-9]*)",', store_script_data).group(1)

            properties = {
                "ref": ref,
                "name": response.xpath(
                    'normalize-space(//*[@itemprop="name"]//text())'
                ).extract_first(),
                "addr_full": response.xpath(
                    'normalize-space(//span[@itemprop="streetAddress"]//text())'
                ).extract_first(),
                "city": response.xpath(
                    'normalize-space(//span[@itemprop="addressLocality"]//text())'
                ).extract_first(),
                "state": response.xpath(
                    'normalize-space(//span[@itemprop="addressRegion"]//text())'
                ).extract_first(),
                "postcode": response.xpath(
                    'normalize-space(//span[@itemprop="postalCode"]//text())'
                ).extract_first(),
                "phone": response.xpath(
                    'normalize-space(//span[@itemprop="telephone"]//text())'
                ).extract_first(),
                "website": response.url,
                "lat": lat,
                "lon": lon,
            }

            yield GeojsonPointItem(**properties)

    def parse_sears_outlet_store(self, response):
        json_data = json.loads(response.text)
        store_data = json_data["storePageData"]["storeInfo"]
        # Ensure ref is consistent across sears sites - 7 digit unique store identifier (zero padded)
        ref = str(store_data["unit"]).zfill(7)

        properties = {
            "ref": ref,
            "name": store_data["storeName"],
            "addr_full": store_data["streetAddr"],
            "city": store_data["city"],
            "state": store_data["state"],
            "postcode": store_data["zip"],
            "phone": store_data.get("phone"),
            "website": "https://www.searsoutlet.com" + store_data.get("url", ""),
            # Lat and lon are unavailable in outlet store responses
        }

        yield GeojsonPointItem(**properties)

    def parse_sears_hts_store(self, response):
        json_data = json.loads(response.text)
        store_data = json_data["store"]
        # Ensure ref is consistent across sears sites - 7 digit unique store identifier (zero padded)
        ref = store_data["name"].zfill(7)

        properties = {
            "ref": ref,
            "name": store_data["custrecord_website_display_name"],
            "addr_full": store_data["custrecord_loc_det_add_1"],
            "city": store_data["custrecord_loc_det_city"],
            "state": store_data["custrecord_loc_det_state_or_province"],
            "postcode": store_data["custrecord_loc_det_zip_or_postal_code"],
            "country": store_data["custrecord_loc_det_country"],
            "phone": store_data.get("custrecord_loc_det_phone"),
            "website": store_data.get("custrecord_loc_det_store_url"),
            "lat": store_data.get("custrecord_sho_latitude"),
            "lon": store_data.get("custrecord_sho_lbi_longitude"),
        }

        yield GeojsonPointItem(**properties)
