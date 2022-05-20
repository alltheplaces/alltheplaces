# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {1: "Mo", 2: "Tu", 3: "We", 4: "Th", 5: "Fr", 6: "Sa", 0: "Su"}


class PigglyWigglySpider(scrapy.Spider):
    """This spider scrapes from two different places, an api which has their stores in Wisconsin
    and Illinois, and a page which has all of their other stores. Cookies are used for the
    api request.
    """

    name = "pigglywiggly"
    item_attributes = {"brand": "Piggly Wiggly", "brand_wikidata": "Q3388303"}
    allowed_domains = ["pigglywiggly.com", "www.shopthepig.com"]

    def start_requests(self):
        url = "https://www.shopthepig.com/api/m_user/sessioninit"
        formdata = {"method": "POST"}
        yield scrapy.FormRequest(url, formdata=formdata, callback=self.parse_wi_token)

        yield scrapy.Request(
            "https://www.pigglywiggly.com/store-locations",
            callback=self.parse_nonwi,
        )

    def parse_wi_hours(self, store_hours):
        opening_hours = OpeningHours()

        for store_day in store_hours:
            day = DAY_MAPPING[store_day.get("day")]
            open_time = store_day.get("open")
            close_time = store_day.get("close")
            if open_time is None and close_time is None:
                continue
            opening_hours.add_range(
                day=day,
                open_time=open_time,
                close_time=close_time,
                time_format="%H:%M%p",
            )

        return opening_hours.as_opening_hours()

    def parse_wi_token(self, response):
        # Get authentication token for api
        csrf = response.text.strip('[""]')

        locations_url = (
            "https://www.shopthepig.com/api/m_store_location?store_type_ids=1,2,3"
        )

        headers = {
            "authority": "www.shopthepig.com",
            "accept-language": "en-US,en;q=0.9",
            "cookie": "__cfduid=d9a8c379f9e4520ce97e2a938504cfd191576252256; has_js=1; SESSb159e7a0d4a6fad9ba3abc7fadef99ec=QdLSe8PB_GYs3I01Do1aBTGK8a04ugH7HGnCO1qTZTY; XSRF-TOKEN={}".format(
                csrf
            ),
            "referer": "https://www.shopthepig.com/",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-csrf-token": "{}".format(csrf),
            "user-agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
        }

        yield scrapy.http.Request(
            url=locations_url, headers=headers, callback=self.parse_wi
        )

    def parse_wi(self, response):
        data = response.json()
        stores = data["stores"]
        for store in stores:
            properties = {
                "ref": store["storeID"],
                "name": store["storeName"],
                "addr_full": store["normalized_address"],
                "city": store["normalized_city"],
                "state": store["normalized_state"],
                "postcode": store["normalized_zip"],
                "lat": store["latitude"],
                "lon": store["longitude"],
                "phone": store["phone"],
                "website": store["webURL"],
            }
            hours = store.get("store_hours")
            if hours:
                properties["opening_hours"] = self.parse_wi_hours(hours)

            yield GeojsonPointItem(**properties)

    def parse_nonwi(self, response):
        for state_url in response.xpath(
            '//div[@class="views-field-province-1"]/span[@class="field-content"]/a/@href'
        ).extract():
            yield scrapy.Request(
                response.urljoin(state_url),
                callback=self.parse_state,
            )

    def parse_state(self, response):
        for location in response.xpath('//li[contains(@class, "views-row")]'):
            # Extract coordinates
            map_link = location.xpath(
                './/a[contains(@href,"maps.google")]/@href'
            ).extract_first()
            if re.search(r".+=([0-9.-]+)\+([0-9.-]+)", map_link):
                lat = re.search(r".+=([0-9.-]+)\+([0-9.-]+)", map_link).group(1)
                lon = re.search(r".+=([0-9.-]+)\+([0-9.-]+)", map_link).group(2)
            else:
                lat = None
                lon = None
            unp = {
                "addr_full": location.xpath(
                    './/div[@class="street-address"]/text()'
                ).extract_first(),
                "city": location.xpath(
                    './/span[@class="locality"]/text()'
                ).extract_first(),
                "state": location.xpath(
                    './/span[@class="region"]/text()'
                ).extract_first(),
                "postcode": location.xpath(
                    './/span[@class="postal-code"]/text()'
                ).extract_first(),
                "phone": location.xpath(
                    './/label[@class="views-label-field-phone-value"]/following-sibling::span[1]/text()'
                ).extract_first(),
                "website": location.xpath(
                    './/label[@class="views-label-field-website-value"]/following-sibling::span[1]/a/@href'
                ).extract_first(),
                "lat": lat,
                "lon": lon,
            }
            if unp["website"]:
                if "google" in unp["website"]:
                    unp["website"] = None

            if unp["phone"]:
                unp["phone"] = unp["phone"].replace(".", "-")

            properties = {}
            for key in unp:
                if unp[key]:
                    properties[key] = unp[key].strip()
            ref = ""
            if "addr_full" in properties:
                ref += properties["addr_full"]
            if "phone" in properties:
                ref += properties["phone"]
            properties["ref"] = ref

            yield GeojsonPointItem(**properties)
