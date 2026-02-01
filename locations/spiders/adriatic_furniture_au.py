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
    rules = [
        Rule(
            LinkExtractor(
                restrict_text="VIEW TRADING HOURS",
                process_value=lambda x: x.replace("adriaticfurniture-au.myshopify.com", "www.adriatic.com.au"),
            ),
            follow=False,
            callback="parse",
        )
    ]

    def parse(self, response: Response) -> Iterable[Feature]:
        store_details = response.xpath('(//div[@class="hdt-ourstore_inner"]/div[@class="hdt-rte"])[1]')
        properties = {
            "ref": response.url,
            "addr_full": merge_address_lines(store_details.xpath("./p[1]//text()").getall()),
            "phone": re.sub(r"Phone\s*:\s*", "", " ".join(store_details.xpath("./p[2]//text()").getall())).strip(),
            "email": re.sub(r"Email\s*:\s*", "", " ".join(store_details.xpath("./p[3]//text()").getall())).strip(),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        if ("VIC" in properties["addr_full"] or "Victoria" in properties["addr_full"]) and not properties[
            "phone"
        ].startswith("0"):
            properties["phone"] = "03 {}".format(properties["phone"])
        hours_text = " ".join(store_details.xpath('//div[@class="timing"]//span/text()').getall())
        properties["opening_hours"].add_ranges_from_string(hours_text)
        extract_google_position(properties, response)
        apply_category(Categories.SHOP_FURNITURE, properties)
        yield Feature(**properties)
