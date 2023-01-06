import re

from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import GeojsonPointItem


def extract_email_link(item, response):
    for link in response.xpath("//a/@href").getall():
        if link.startswith("mailto:"):
            item["email"] = link.replace("mailto:", "").strip()
            return


def extract_phone_link(item, response):
    for link in response.xpath("//a/@href").getall():
        if link.startswith("tel:"):
            item["phone"] = link.replace("tel:", "").strip()
            return


def clean_address(addr):
    if isinstance(addr, str):
        addr = addr.replace("\n", ",").replace("\r", ",").replace("\t", ",").replace("\f", ",")
        addr = addr.split(",")

    if not isinstance(addr, list):
        return

    return_addr = []

    for line in addr:
        if line:
            line = line.replace("(null)", "")
            line = line.strip("\n\r\t\f ,")
            if line != "":
                return_addr.append(line)

    return ", ".join(return_addr)


class VapeStoreGB(SitemapSpider):
    name = "vapestore_gb"
    item_attributes = {"brand": "vapestore"}
    sitemap_urls = ["https://www.vapestore.co.uk/pub/sitemap/vapestore_sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.vapestore\.co\.uk\/vapestore-([-\w]+)", "parse")]
    download_delay = 5

    def sitemap_filter(self, entries):
        for entry in entries:
            if entry["loc"] != "https://www.vapestore.co.uk/vapestore-index":
                yield entry

    def parse(self, response, **kwargs):
        item = GeojsonPointItem()

        item["ref"] = re.match(self.sitemap_rules[0][0], response.url).group(1)
        item["website"] = response.url

        item["name"] = response.xpath('//div[@class="flt_left"]/strong/text()').get()
        item["addr_full"] = clean_address(response.xpath('//div[@class="flt_left"]/text()').getall())

        item["country"] = "GB"

        extract_email_link(item, response)
        extract_google_position(item, response)

        return item
