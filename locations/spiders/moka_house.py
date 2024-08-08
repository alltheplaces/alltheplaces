import re

import scrapy

from locations.items import Feature


class MokaHouseSpider(scrapy.Spider):
    name = "moka_house"
    item_attributes = {"brand": "Moka House"}
    allowed_domains = ["mokahouse.com"]
    start_urls = ("http://mokahouse.com/locations/",)

    def parse(self, response):
        links = response.xpath('//div[@class="entry-summary"]/p/a')

        for link in links:
            if link == links[-1]:
                continue
            name = re.search(r"(.*)(\s\(.*\))", link.xpath("text()").extract_first()).groups()[0]
            yield scrapy.Request(
                link.xpath("@href").extract_first(),
                meta={"name": name},
                callback=self.parse_link,
            )

    def parse_link(self, response):
        ref = response.xpath('//div[@class="article-wrapper"]/article/@id').extract_first()
        name = response.meta["name"]
        website = response.url

        tmp_data = response.xpath('//div[@class="entry-summary"]/p')
        p_2 = tmp_data[1].xpath("text()").extract()
        p_3 = tmp_data[2].xpath("text()").extract()
        p_4 = tmp_data[3].xpath("text()").extract()
        p_5 = tmp_data[4].xpath("text()").extract()
        l_address = p_2 + p_3
        l_address = [x for x in l_address if x != "\n"]
        address_text = "".join(l_address).replace("\n", ", ")
        address_data = re.search(r"(.*)(,\s)(.*)(\sBC)(.*)", address_text).groups()
        street = address_data[0].strip()
        city = address_data[2].replace(",", "").strip()
        state = address_data[3].strip()
        postcode = address_data[4].strip()

        tmp_data_extract = tmp_data.extract()
        phone_text = tmp_data_extract[2] + tmp_data_extract[3]
        phone_number = ""
        match = re.search(r"<strong>P:\s(.*)<\/strong>", phone_text)
        if match is not None:
            phone_number = match.groups()[0]

        l_hours = p_4 + p_5
        l_hours = [x.replace("\n", "") for x in l_hours if x != "\n" and self.has_digit(x)]
        opening_hours = ";".join(l_hours)

        properties = {
            "ref": ref,
            "name": name,
            "website": website,
            "phone": phone_number,
            "street": street,
            "city": city,
            "state": state,
            "postcode": postcode,
            "opening_hours": opening_hours,
        }

        yield Feature(**properties)

    def has_digit(self, str):
        return bool(re.search(r"\d", str))
