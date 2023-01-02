import re
import urllib.parse

import scrapy

from locations.categories import Categories, apply_category
from locations.items import GeojsonPointItem


class TeslaSpider(scrapy.Spider):
    name = "tesla"
    item_attributes = {"brand": "Tesla", "brand_wikidata": "Q478214"}
    allowed_domains = ["www.tesla.com"]
    start_urls = [
        "https://www.tesla.com/findus/list",
    ]
    download_delay = 0.5
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
    }

    def parse(self, response):
        # Only scrape stores and service centers. Pass through set to deduplicate the country URLs.
        # Some countries appear twice on the page (like US).
        country_urls = set(
            response.xpath(
                '//a[contains(@href,"stores") or contains(@href,"services") or contains(@href,"superchargers")]/@href'
            ).extract()
        )
        for country_url in country_urls:
            yield scrapy.Request(response.urljoin(country_url), callback=self.parse_store_list)

    def parse_store_list(self, response):
        store_urls = response.xpath("//address/a/@href").extract()
        for store_url in store_urls:
            yield scrapy.Request(response.urljoin(store_url), callback=self.parse_store)

    def parse_store(self, response):
        # Skip if "Coming Soon" - no content to capture yet
        if response.xpath('//span[@class="coming-soon"]/text()').extract_first() == "Coming Soon":
            return

        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

        # city, state, and zip do not have separate classes - contained together in locality class as text
        name = response.xpath("normalize-space(//header/h1/text())").extract_first()
        common_name = response.xpath('normalize-space(//span[@class="common-name"]//text())').extract_first()
        street_address = response.xpath('normalize-space(//span[@class="street-address"]//text())').extract_first()
        city_state_zip = response.xpath('normalize-space(//span[@class="locality"]//text())').extract_first()

        if common_name and street_address and city_state_zip:
            addr_full = common_name + " " + street_address + ", " + city_state_zip
        elif street_address and not city_state_zip:
            addr_full = street_address
        elif city_state_zip and not street_address:
            addr_full = city_state_zip
        elif street_address and city_state_zip:
            addr_full = street_address + ", " + city_state_zip
        else:
            addr_full = None

        country_url = response.xpath('//header[@class="findus-list-header"]/a/@href').extract_first()
        country = urllib.parse.unquote_plus(re.search(r".+/(.+?)/?(?:\.html|$)", country_url).group(1))
        phone = response.xpath('normalize-space(//span[@class="tel"]/span[2]/text())').extract_first()
        location_type = re.search(r".+/(.+?)/(.+?)/?(?:\.html|$)", response.url).group(1)

        # map link varies across store pages
        if response.xpath('normalize-space(//a[contains(@href,"maps.google")]/@href)').extract_first():
            map_link = response.xpath('normalize-space(//a[contains(@href,"maps.google")]/@href)').extract_first()
        else:
            map_link = response.xpath('normalize-space(//img[contains(@src,"maps.google")]/@src)').extract_first()

        # extract coordinates from map link
        if re.search(r".+=([0-9.-]+),\s?([0-9.-]+)", map_link):
            lat = re.search(r".+=([0-9.-]+),\s?([0-9.-]+)", map_link).group(1)
            lon = re.search(r".+=([0-9.-]+),\s?([0-9.-]+)", map_link).group(2)
        elif re.search(r".+@([0-9.-]+),\s?([0-9.-]+)", map_link):
            lat = re.search(r".+@([0-9.-]+),\s?([0-9.-]+)", map_link).group(1)
            lon = re.search(r".+@([0-9.-]+),\s?([0-9.-]+)", map_link).group(2)
        else:
            lat = None
            lon = None

        properties = {
            "ref": ref,
            "name": name,
            "addr_full": addr_full,
            "street_address": street_address,
            "country": country,
            "phone": phone,
            "website": response.url,
            "lat": lat,
            "lon": lon,
        }

        if location_type == "supercharger":
            apply_category(Categories.CHARGING_STATION, properties)
            properties["brand_wikidata"] = "Q17089620"
            properties["brand"] = "Tesla Supercharger"
        elif location_type == "store":
            apply_category(Categories.SHOP_CAR, properties)
        elif location_type == "service":
            apply_category(Categories.SHOP_CAR_REPAIR, properties)
        else:
            properties["extras"] = {"location_type": location_type}

        yield GeojsonPointItem(**properties)
