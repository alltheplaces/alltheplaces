from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class GoodyearAutocareAUSpider(SitemapSpider):
    name = "goodyear_autocare_au"
    item_attributes = {"brand": "Goodyear", "brand_wikidata": "Q620875"}
    allowed_domains = ["www.goodyear.com.au"]
    sitemap_urls = ["https://www.goodyear.com.au/store-sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.goodyear\.com\.au\/store-locator\/goodyear-autocare-[\w\-]+$", "parse")]

    def parse(self, response: Response) -> Iterable[Feature]:
        properties = {
            "ref": response.url,
            "branch": response.xpath("//h1/text()").get().removeprefix("Goodyear Autocare "),
            "addr_full": merge_address_lines(
                response.xpath('//p[contains(@class, "address-container")]//text()').getall()
            ),
            "phone": response.xpath('//div[contains(@class, "store-phone-custom")]/a/@href').get().removeprefix("tel:"),
            "email": response.xpath('//div[contains(@class, "store-email-custom")]/a/@href')
            .get()
            .removeprefix("mailto:"),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        extract_google_position(properties, response)
        hours_text = " ".join(
            response.xpath(
                '//div[contains(@class, "product-details-block")]//div[contains(@class, "store-day-hours-container")]//text()'
            ).getall()
        )
        properties["opening_hours"].add_ranges_from_string(hours_text)
        apply_category(Categories.SHOP_TYRES, properties)
        yield Feature(**properties)
