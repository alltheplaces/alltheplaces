import json
import re

import scrapy

from locations.items import Feature

regex = r"\[{.*}\]"


class VapianoUSSpider(scrapy.Spider):
    name = "vapiano_us"
    item_attributes = {"brand": "Vapiano", "brand_wikidata": "Q506252"}
    allowed_domains = ["us.vapiano.com"]
    download_delay = 0
    start_urls = ["https://us.vapiano.com/en/restaurants/"]

    def parse(self, response):
        script = response.xpath('//script[contains(., "var restaurants")]/text()')[0].extract()

        data = re.search(regex, script).group()
        data = json.loads(data)

        for i in data:
            name = i["address"]
            city = i["city"]
            street = i["address2"]
            state = i["zip"]  # sometimes includes state
            phone = i["telephone"]
            lat = i["latitude"]
            lon = i["longitude"]
            website = "https://us.vapiano.com/" + i["detailLink"].replace("\\", "")
            country = i["country"]
            addr_full = "{} {}, {}".format(city, street, state)

            yield Feature(
                ref=name,
                city=city,
                street=street,
                country=country,
                addr_full=addr_full,
                phone=phone,
                lat=lat,
                lon=lon,
                website=website,
            )
