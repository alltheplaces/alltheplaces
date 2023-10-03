import re

from scrapy import Request

from locations.spiders.mcdonalds import McDonaldsSpider
from locations.structured_data_spider import StructuredDataSpider


class McDonaldsLUSpider(StructuredDataSpider):
    name = "mcdonalds_lu"
    item_attributes = McDonaldsSpider.item_attributes
    allowed_domains = ["mcd.lu"]
    start_urls = ["https://mcd.lu/"]

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

    def parse(self, response, **kwargs):
        for ref in response.xpath('//a[starts-with(@id, "snav_1_")]/@id').getall():
            yield Request(
                "https://mcd.lu/content.php?r={}&lang=de".format(ref.replace("snav_", "")), callback=self.parse_sd
            )

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = None
        item["addr_full"] = self.parse_address(response.text)
        item["phone"] = self.parse_phone(response.text)
        item["lat"], item["lon"] = self.parse_latlon(response.text)

        yield item
