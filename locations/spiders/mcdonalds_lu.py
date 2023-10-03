import re

import scrapy

from locations.items import Feature
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsLUSpider(scrapy.Spider):
    name = "mcdonalds_lu"
    item_attributes = McDonaldsSpider.item_attributes
    allowed_domains = ["mcd.lu"]
    start_urls = ["https://mcd.lu/"]

    # TODO: There is opening hours, but no good way to grab it as there is a lot of commented out hours around it.

    def parse_name(self, name):
        match = re.search(r'<h1 itemprop="name">(.*)</h1>', name)
        if match:
            return match.groups()[0].strip()
        else:
            return None

    def parse_latlon(self, data):
        match = re.search(r"sll=(.*),(.*)&amp;ss", data)
        if match:
            return match.groups()[0].strip(), match.groups()[1].strip()
        else:
            return None, None

    def parse_phone(self, phone):
        match = re.search(r'Tel <span itemprop="telephone" content="(.*)">', phone)
        if match:
            return match.groups()[0].strip()
        else:
            return None

    def parse_address(self, address):
        address = address[address.find("<h2>Adresse</h2>") + 16 : address.find("Tel")]
        match = re.sub("<[^<]+?>", "", address)
        return " ".join(match.split())

    def parse_store(self, response):
        data = response.text
        name = self.parse_name(data)
        address = self.parse_address(data)
        phone = self.parse_phone(data)
        lat, lon = self.parse_latlon(data)
        properties = {
            "ref": response.meta["ref"],
            "phone": phone,
            "lon": lon,
            "lat": lat,
            "name": name,
            "addr_full": address,
            "country": "lu",
        }

        yield Feature(**properties)

    def parse(self, response):
        matches = re.finditer(r"<a id=\"snav_(1_\d+)\">", response.text)
        for matchNum, match in enumerate(matches):
            ref = match.groups()[0]
            headers = {"User-Agent": "PostmanRuntime/7.29.0"}
            yield scrapy.Request(
                "https://mcd.lu/content.php?r=" + ref + "&lang=de",
                meta={"ref": ref},
                headers=headers,
                callback=self.parse_store,
            )
