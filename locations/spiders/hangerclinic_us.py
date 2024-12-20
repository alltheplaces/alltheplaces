from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class HangerclinicUSSpider(SitemapSpider):
    name = "hangerclinic_us"
    item_attributes = {"brand": "Hanger Clinic"}
    sitemap_urls = [
        "https://hangerclinic.com/locations-sitemap.xml",
    ]
    sitemap_rules = [(r"/clinics/[^/]+/[^/]+/[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["name"] = response.xpath('//*[@class = "c-page-header__title"]/span/text()').get()
        item["street_address"] = response.xpath('//*[@class="c-map__info--address"]/text()').get().strip()
        item["addr_full"] = response.xpath('//*[@class="c-map__info--address"]').xpath("normalize-space()").get()
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["ref"] = item["website"] = response.url
        apply_category(Categories.CLINIC, item)
        extract_google_position(item, response)
        hours_string = response.xpath('//*[@class="c-map__info--hours"]/p/text()').get()
        item["opening_hours"] = OpeningHours()
        if hours_string:
            item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
