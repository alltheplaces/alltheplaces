import re

from scrapy import Request

from locations.spiders.mcdonalds import McdonaldsSpider
from locations.structured_data_spider import StructuredDataSpider


class McdonaldsLUSpider(StructuredDataSpider):
    name = "mcdonalds_lu"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["mcd.lu"]
    start_urls = ["https://mcd.lu/"]

    def parse_latlon(self, data):
        match = re.search(r"sll=(.*),(.*)&amp;ss", data)
        if match:
            return match.groups()[0].strip(), match.groups()[1].strip()
        else:
            return None, None

    def parse(self, response, **kwargs):
        for ref in response.xpath('//a[starts-with(@id, "snav_1_")]/@id').getall():
            yield Request(
                "https://mcd.lu/content.php?r={}&lang=de".format(ref.replace("snav_", "")), callback=self.parse_sd
            )

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = None
        item["addr_full"] = " ".join(
            filter(None, map(str.strip, response.xpath('//div[@class="txt"]/h2/following::text()').getall()))
        ).split(" Tel ", 1)[0]
        item["lat"], item["lon"] = self.parse_latlon(response.text)

        yield item
