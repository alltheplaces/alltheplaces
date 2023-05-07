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
        infos = response.xpath("string(/html/body/div[2]/div/main/article/div[1]/div[2]/div/div/div[2])").get()
        address_full = infos.split("\n")[0]
        address = infos.split("\n")[1]
        state = re.findall("[A-Z]{2}", address)[0]
        postcode = re.findall("[0-9]{5}|[A-Z0-9]{3} [A-Z0-9]{3}", address)[0]
        city = address.replace(state, "").replace(postcode, "").strip().replace(",", "")

        name = response.xpath('//h1[@class="x-text-content-text-primary"]/text()').get()
        phone = response.xpath('//a[@class="studio-contact-phone"]/text()').get()
        facebook = response.xpath('//a[contains(@href, "facebook")]/@href').get()
        ref = response.request.url.replace(self.start_urls[0], "_")
        email = self.decodeEmail(
            response.xpath('//a[@class="studio-contact-email"]/@href').get().replace("/cdn-cgi/l/email-protection#", "")
        )

        properties = {
            "name": name,
            "ref": ref,
            "street_address": address_full,
            "city": city,
            "state": state,
            "postcode": postcode,
            "phone": phone,
            "email": email,
            "facebook": facebook,
            "website": response.url,
        }

        yield Feature(**properties)
