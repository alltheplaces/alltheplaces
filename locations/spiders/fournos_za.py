import re

import scrapy
from scrapy.selector import Selector

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.outdoor_supply_hardware_us import decode_email


class FournosZASpider(scrapy.Spider):
    name = "fournos_za"
    start_urls = ["https://www.fournos.co.za/find-us.php"]
    item_attributes = {
        "brand": "Fournos Bakery",
        "brand_wikidata": "Q116740976",
    }

    def parse(self, response):
        for loc in response.xpath("//div[contains(@class, 'pum-container')]"):
            item = Feature()
            extract_google_position(item, loc)
            item["ref"] = loc.xpath("./@id").get("").replace("popmake-", "")
            item["branch"] = loc.xpath(".//div[contains(@class,'pum-title')]/text()").get("").strip()

            encoded = loc.xpath(".//span[@class='__cf_email__']/@data-cfemail").get()
            if encoded:
                item["email"] = decode_email(encoded)
            else:
                item["email"] = None

            item["phone"] = loc.xpath('.//a[contains(@href, "tel:")]/@href').get("").replace("tel:", "")
            item["addr_full"] = clean_address(
                loc.xpath(".//p[strong[contains(., 'Email')]]/following-sibling::p[.//br][1]//text()").getall()
            ).rstrip(".")

            item["opening_hours"] = self.parse_hours(loc)
            yield item

    def parse_hours(self, loc: Selector) -> OpeningHours:
        oh = OpeningHours()
        for rule in loc.xpath(".//p[normalize-space() != '\xa0'][last()]//text()").getall():
            oh.add_ranges_from_string(re.sub(r"(\d)h(\d)", r"\1:\2", rule))
        return oh
