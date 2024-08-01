import re

import scrapy

from locations.items import Feature


class BarMethodSpider(scrapy.Spider):
    name = "bar_method"
    item_attributes = {"brand": "The Bar Method", "brand_wikidata": "Q117599728"}
    allowed_domains = ["barmethod.com"]
    start_urls = ("https://barmethod.com/locations/",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//a[@class="studioname"]/@href').extract()
        for path in city_urls:
            if path == "https://barmethod.com/locations/bar-online/":
                continue
            yield scrapy.Request(
                path.strip(),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        infos = response.xpath("string(/html/body/div/div/main/article/div[1]/div[2]/div/div/div[2])").get().split("\n")

        street_address = infos[0]

        match = re.match(r"^([^,]*), (\w{2}) *(\d{5})?$", infos[1])
        if match is not None:
            # US
            city = match.group(1).strip()
            state = match.group(2).strip()
            postcode = match.group(3).strip() if len(match.groups()) > 2 else None
            country = "US"
        else:
            # CA
            match = re.match(r"^([^,]*), (\w{2}) *(\w{3} \w{3})?$", infos[1])
            city = match.group(1).strip()
            state = match.group(2).strip()
            postcode = match.group(3).strip() if len(match.groups()) > 2 else None
            country = "CA"

        email = infos[2]
        phone = infos[3]

        name = response.xpath('//h1[@class="x-text-content-text-primary"]/text()').get()
        facebook = response.xpath('//a[contains(@href, "facebook")]/@href').get()
        ref = response.request.url.replace(self.start_urls[0], "_")

        properties = {
            "name": name,
            "ref": ref.strip("_/"),
            "street_address": street_address,
            "city": city,
            "state": state,
            "postcode": postcode,
            "country": country,
            "phone": phone,
            "email": email,
            "facebook": facebook,
            "website": response.url,
        }

        yield Feature(**properties)
