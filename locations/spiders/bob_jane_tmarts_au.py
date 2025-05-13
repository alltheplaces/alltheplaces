from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BobJaneTmartsAUSpider(SitemapSpider):
    name = "bob_jane_tmarts_au"
    item_attributes = {"brand_wikidata": "Q16952468"}
    allowed_domains = ["www.bobjane.com.au"]
    sitemap_urls = ["https://www.bobjane.com.au/sitemap.xml"]
    sitemap_rules = [
        (r"^https:\/\/www\.bobjane\.com\.au\/pages\/[\w\-]+-t-marts$", "parse"),
    ]

    def parse(self, response: Response) -> Iterable[Feature]:
        if not response.xpath('//div[@class="store-info"]'):
            # Some store pages are blank and should be ignored.
            return
        properties = {
            "ref": response.url,
            "branch": response.xpath('//div[@class="store-info"]/h2/text()').get(),
            "addr_full": merge_address_lines(
                response.xpath(
                    '//div[@class="store-info"]/div[@class="store-address"]/p[1]/text()[position()>1]'
                ).getall()
            ),
            "phone": response.xpath(
                '//div[@class="store-info"]/div[@class="store-address"]/p[1]/a[contains(@href, "tel:")]/@href'
            )
            .get("")
            .replace("tel:", ""),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        hours_text = (
            " ".join(response.xpath('//div[@class="store-info"]/*[self::p or self::h4]/text()').getall())
            .upper()
            .split("TRADING HOURS:", 1)[1]
        )
        properties["opening_hours"].add_ranges_from_string(hours_text)
        extract_google_position(properties, response)
        apply_category(Categories.SHOP_TYRES, properties)
        yield Feature(**properties)
