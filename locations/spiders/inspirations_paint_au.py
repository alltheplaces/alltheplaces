from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.pipelines.address_clean_up import merge_address_lines


class InspirationsPaintAUSpider(SitemapSpider):
    name = "inspirations_paint_au"
    item_attributes = {"brand": "Inspirations Paint", "brand_wikidata": "Q140574451"}
    allowed_domains = ["www.inspirationspaint.com.au"]
    sitemap_urls = ["https://www.inspirationspaint.com.au/documents/sitemap-stores.xml"]
    sitemap_rules = [(r"^https:\/\/www\.inspirationspaint\.com\.au\/store-locations(?:\/[\w+\-]+){2}", "parse")]

    def parse(self, response) -> Iterable[Feature]:
        # Note: LD+JSON appears on some but NOT ALL store pages. This spider
        # therefore needs to implement HTML parsing as the fallback, using
        # LD+JSON if it exists for geographic coordinates. Coordinates are not
        # otherwise avaialble outside of LD+JSON as HTML pages embed a Google
        # Maps page via Google Place ID.
        properties = {
            "ref": response.url,
            "addr_full": merge_address_lines(response.xpath('//div[contains(@class, "store-address")]/span[@class="address"]/text()').getall()),
            "phone": response.xpath('//div[contains(@class, "store-contact")]/a[contains(@href, "tel:")]/@href').get().removeprefix("tel:"),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }

        hours_string = " ".join(response.xpath('//div[contains(@class, "trading-hours")]//text()').getall())
        properties["opening_hours"].add_ranges_from_string(hours_string)

        if ldjson := LinkedDataParser.find_linked_data(response, "LocalBusiness"):
            ldjson_item = LinkedDataParser.parse_ld(ldjson, "%I:%M%p")
            properties["lat"] = ldjson_item["lat"]
            properties["lon"] = ldjson_item["lon"]
            properties["street_address"] = ldjson_item["street_address"]
            properties["city"] = ldjson_item["city"].title()
            properties["state"] = ldjson_item["state"].upper()

        apply_category(Categories.SHOP_PAINT, properties)

        yield Feature(**properties)
