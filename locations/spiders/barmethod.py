import re

import scrapy

from locations.items import Feature


class BarMethodSpider(scrapy.Spider):
    name = "barmethod"
    item_attributes = {"brand": "The Bar Method", "brand_wikidata": "Q117599728"}
    allowed_domains = ["barmethod.com"]
    start_urls = ("https://barmethod.com/locations/",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//a[@class="studioname"]/@href').extract()
        for path in city_urls:
            yield scrapy.Request(
                path.strip(),
                callback=self.parse_store,
            )

    def decodeEmail(self, protectedEmail):
        decode = ""
        k = int(protectedEmail[:2], 16)

        for i in range(2, len(protectedEmail) - 1, 2):
            decode += chr(int(protectedEmail[i : i + 2], 16) ^ k)

        return decode

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
            match = re.match(r"^([^,]*), (\w{2}) *([\w\d]{3} [\w\d]{3})?$", infos[1])
            city = match.group(1).strip()
            state = match.group(2).strip()
            postcode = match.group(3).strip() if len(match.groups()) > 2 else None
            country = "CA"

        email = infos[2]
        phone = infos[3]
        # state = re.findall("[A-Z]{2}", address)[0]
        # address = infos.split("\n")[1]
        # postcode = re.findall("[0-9]{5}|[A-Z0-9]{3} [A-Z0-9]{3}", address)[0]
        # city = address.replace(state, "").replace(postcode, "").strip().replace(",", "")

        name = response.xpath('//h1[@class="x-text-content-text-primary"]/text()').get()
        facebook = response.xpath('//a[contains(@href, "facebook")]/@href').get()
        ref = response.request.url.replace(self.start_urls[0], "_")

        properties = {
            "name": name,
            "ref": ref,
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
