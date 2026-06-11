import re
from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class AdriaticFurnitureAUSpider(CrawlSpider):
    name = "adriatic_furniture_au"
    item_attributes = {"brand": "Adriatic Furniture", "brand_wikidata": "Q117856796"}
    allowed_domains = ["www.adriatic.com.au"]
    start_urls = ["https://www.adriatic.com.au/pages/store-locator"]

    rules = [Rule(LinkExtractor(allow=r"/pages/[a-z0-9\-]+$"), follow=False, callback="parse_store")]

    def parse_store(self, response: Response) -> Iterable[Feature]:
        store_details = response.xpath(
            '(//div[contains(@class, "hdt-ourstore_inner")]/div[contains(@class, "hdt-rte")])[1]'
        )
        if not store_details:
            return

        if phone_match_link := store_details.xpath('.//a[contains(@href, "tel:")]/@href').get():
            phone = phone_match_link.replace("tel:", "").strip()
        else:
            contact_text = " ".join(store_details.xpath(".//text()").getall())
            phone = re.search(r"\(?03\)?[\s\-]*\d{4}[\s\-]*\d{4}", contact_text).group(0).strip()

        properties = {
            "ref": response.url,
            "branch": response.xpath("normalize-space(//title/text())")
            .get("")
            .split("|")[0]
            .replace("Furniture Store", "")
            .strip(),
            "phone": phone,
            "email": store_details.xpath('.//a[contains(@href, "mailto:")]/@href').get().replace("mailto:", "").strip(),
            "website": response.url,
            "addr_full": merge_address_lines(store_details.xpath("./p[1]//text()").getall()),
        }

        if not properties["phone"].startswith(("0", "(")):
            properties["phone"] = "03 {}".format(properties["phone"])

        if map_wrapper := response.xpath('//div[contains(@class, "hdt-map-inner")]'):
            extract_google_position(properties, map_wrapper[0])

            oh = OpeningHours()
            if timing_block := response.xpath('//div[contains(@class, "timing")]'):
                for row in timing_block.xpath(".//li"):
                    day = row.xpath("./span[1]/text()").get()
                    hours = row.xpath("./span[2]/text()").get()
                    if day and hours:
                        oh.add_ranges_from_string(f"{day}: {hours}")

                properties["opening_hours"] = oh

        apply_category(Categories.SHOP_FURNITURE, properties)
        yield Feature(**properties)
