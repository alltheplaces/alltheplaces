from collections.abc import Iterable
from typing import Any

from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, PaymentMethods, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.structured_data_spider import extract_email, extract_facebook, extract_phone


class RedcrossGBSpider(SitemapSpider):
    name = "redcross_gb"
    item_attributes = {"brand": "British Red Cross", "brand_wikidata": "Q4970966"}
    sitemap_urls = ["https://www.redcross.org.uk/sitemap.xml"]
    sitemap_rules = [("/find-a-charity-shop/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # Remove closed shops pages
        if "this shop has closed" in response.text.lower():
            return

        item = Feature()
        item["ref"] = item["website"] = response.url

        # Name and branch
        item["name"] = "British Red Cross"
        if h1 := response.xpath("normalize-space(//main//h1[1]/text())").get():
            item["branch"] = h1.replace("Red Cross charity shop in ", "").strip()

        # Address
        raw_lines = response.xpath(
            '//bdi[contains(concat(" ", normalize-space(@class), " "), " brc-address ")]//p//text()[normalize-space()]'
        ).getall()

        if addr_full := clean_address(raw_lines):
            item["addr_full"] = addr_full

        if raw_lines:
            item["street_address"] = clean_address([raw_lines[0]])

        # Contact
        main_nodes = Selector(text=response.text).xpath("//main")
        if main_selector := main_nodes[0]:
            extract_phone(item, main_selector)
            extract_email(item, main_selector)
            extract_facebook(item, main_selector)

        # Opening hours
        hours = OpeningHours()
        for row in response.xpath('//h2[@id="opening-hours"]/following::*[self::dl][1]//dt'):
            day = row.xpath("normalize-space(.//text())").get()
            value = row.xpath("normalize-space(following-sibling::dd[1])").get()
            if not day or not value:
                continue
            hours.add_ranges_from_string(f"{day} {value}")
        if hours:
            item["opening_hours"] = hours.as_opening_hours()

        # Attributes
        shop_info = response.xpath('//h2[@id="shop-information"]/following::ul[1]/li/text()').getall()
        shop_info = [s.strip() for s in shop_info if s and s.strip()]
        if any("card payment" in s.lower() for s in shop_info):
            item["extras"][PaymentMethods.CARDS.value] = "yes"

        # Category
        apply_category(Categories.SHOP_CHARITY, item)
        # Extract geo-coordinates from Google Maps iframe
        extract_google_position(item, response)
        yield item
