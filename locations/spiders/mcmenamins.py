import re

import scrapy

from locations.google_url import extract_google_position
from locations.items import Feature

DAYS = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Friday": "Fr",
    "Thursday": "Th",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class McmenaminsSpider(scrapy.Spider):
    name = "mcmenamins"
    item_attributes = {"brand": "McMenamins", "brand_wikidata": "Q6802345"}
    allowed_domains = ["mcmenamins.com"]
    start_urls = ("https://www.mcmenamins.com/eat-drink",)

    def store_hours(self, store_hours):
        result = ""
        for line in store_hours:
            sl = re.search(
                r"(\w+)\s*(through|and|-|&|–)?\s*(\w+)?,\s*(\d+):?(\d+)?\s*((a\.m\.)|(p\.m\.)|noon|midnight)\s*\'til\s*(\d+):?(\d+)?\s*((a\.m\.)|(p\.m\.)|noon|midnight)",
                line,
            )

            if not sl:
                continue
            if sl[3] == "daily" or sl[1] == "daily":
                result += "Mo-Su "
            else:
                result += DAYS[sl[1]] + (("-" + DAYS[sl[3]]) if sl[3] else "") + " "

            i = int(sl[4])

            if sl[6] == "a.m." or sl[6] == "noon":
                result += "{:02d}".format(int(sl[4]))
            else:
                result += "{:02d}".format(i + 12)

            if sl[5]:
                result += ":" + sl[5] + "-"
            else:
                result += ":00" + "-"

            i = int(sl[9])

            if sl[11] == "midnight":
                result += "00"
            elif sl[9] == "a.m." or sl[6] == "noon":
                result += "{:02d}".format(int(sl[9]))
            else:
                result += "{:02d}".format(i + 12)

            if sl[10]:
                result += ":" + sl[10] + "; "
            else:
                result += ":00" + "; "

        return result.rstrip("; ")

    def phone_normalize(self, phone):
        r = re.search(
            r"\+?(\s+)*(\d{1})?(\s|\()*(\d{3})(\s+|\))*(\d{3})(\s+|-)?(\d{2})(\s+|-)?(\d{2})",
            phone,
        )
        return ("(" + r.group(4) + ") " + r.group(6) + "-" + r.group(8) + "-" + r.group(10)) if r else phone

    def parse(self, response):
        # high-level list of states
        shops = response.xpath('//div[@id="MainContent_eatDrinkLocations"]/div[contains(@class,"all")]')

        for path in shops:
            yield scrapy.Request(
                response.urljoin(path.xpath('.//div/div[@class="tm-panel-titlebg"]/a/@href').extract_first()),
                callback=self.parse_store,
                meta={
                    "ref": path.xpath(".//@id").extract_first(),
                },
            )

    def parse_store(self, response):
        address_full = response.xpath('//div[@class="mcm-logo-address"]')[0].xpath(".//a/p/text()").extract_first()
        address_parts = re.match(r"(.{3,}),\s?(.{3,}),\s?(\w{2}) (\d{5})", address_full)

        properties = {
            "ref": response.meta.get("ref"),
            "website": response.url,
            "addr_full": address_parts[1].strip(),
            "city": address_parts[2].strip(),
            "state": address_parts[3].strip(),
            "postcode": address_parts[4].strip(),
            "phone": self.phone_normalize(
                response.xpath('//div[@class="mcm-logo-address"]')[0].xpath(".//ul/li/a/@href").extract_first()
            ),
            "opening_hours": self.store_hours(response.xpath('//div[@id="MainContent_hoursText"]/p/text()').extract()),
        }
        extract_google_position(properties, response)

        yield Feature(**properties)
