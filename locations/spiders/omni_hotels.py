from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class OmniHotelsSpider(SitemapSpider, PlaywrightSpider):
    name = "omni_hotels"
    item_attributes = {"brand": "Omni Hotels", "brand_wikidata": "Q7090329"}
    sitemap_urls = ["https://www.omnihotels.com/sitemap.xml"]
    sitemap_rules = [(r"/property-details$", "parse")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["name"] = response.xpath('//*[@class="hotelName"]/text()').get()
        item["addr_full"] = clean_address(
            response.xpath('//*[contains(@class, "plp-contact-link")]/text()').getall()[0:4]
        )
        item["phone"] = response.xpath('//a[@class="tel_link"]/span/text()').get()
        extract_google_position(item, response)
        apply_category(Categories.HOTEL, item)
        yield item
