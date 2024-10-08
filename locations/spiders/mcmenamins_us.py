import re

import scrapy

from locations.categories import Categories
from locations.google_url import extract_google_position
from locations.hours import DAYS
from locations.items import Feature


class McmenaminsUSSpider(scrapy.Spider):
    name = "mcmenamins_us"
    item_attributes = {
        "brand": "McMenamins",
        "brand_wikidata": "Q6802345",
        "extras": Categories.PUB.value,
    }
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
        content = response.xpath('//div[@id="property_bar_address_no_button" or @id="property_bar_address"]')
        info = content.xpath("(nobr|.)/a/@href").extract()

        address_parts = re.match(r"^http:\/\/maps.google.com\/\?q=(.*),([^,]*),\s+(.*),\s+(\d{5})$", info[0])

        properties = {
            "ref": response.meta.get("ref"),
            "website": response.url,
            "street_address": address_parts.group(1).strip(),
            "city": address_parts.group(2).strip(),
            "state": address_parts.group(3).strip(),
            "postcode": address_parts.group(4).strip(),
            "phone": self.phone_normalize(info[1]),
            "opening_hours": self.store_hours(response.xpath('//div[@id="MainContent_hoursText"]/p/text()').extract()),
        }
        extract_google_position(properties, response)

        yield Feature(**properties)
