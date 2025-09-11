import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class HotelBbSpider(SitemapSpider, StructuredDataSpider):
    name = "hotel_bb"
    BB_HOTELS = {"brand": "B&B Hotels", "brand_wikidata": "Q794939"}
    sitemap_urls = ["https://www.hotel-bb.com/sitemap.xml"]
    sitemap_rules = [("/en/hotel/", "parse_sd")]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if item["name"].upper().startswith("B&B HOTEL"):
            item["branch"] = re.sub("B&B HOTELS?", "", item.pop("name"), re.IGNORECASE).strip()
            item.update(self.BB_HOTELS)

        item["lat"], item["lon"] = response.xpath('//*[@class="location"]/@value').get().split(",")
        item["phone"] = response.xpath('//div[@class="phone-contact external-phone"]/text()').get()
        item["email"] = response.xpath('//div[contains(@class, "field--name-field-email")]/text()').get()

        for link in response.xpath(
            '//div[@class="combo-selectbox__item language"]//a[contains(@class, "language-link")]'
        ):
            item["extras"]["website:{}".format(link.xpath("@hreflang").get())] = response.urljoin(
                link.xpath("@href").get()
            )

        apply_category(Categories.HOTEL, item)

        yield item
