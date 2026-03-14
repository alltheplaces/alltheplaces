from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class LoungesGBSpider(SitemapSpider):
    name = "lounges_gb"
    item_attributes = {"brand": "Lounges", "brand_wikidata": "Q114313933"}
    sitemap_urls = ["https://thelounges.co.uk/robots.txt"]
    sitemap_rules = [(r"https://thelounges.co.uk/[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath("//h1/span/text()").get()
        item["addr_full"] = (
            response.xpath('//*[contains(@class ,"title-section__address-section")]').xpath("normalize-space()").get()
        )
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["email"] = response.xpath('//*[contains(@href,"mailto:")]/text()').get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        apply_category(Categories.RESTAURANT, item)
        item["opening_hours"] = OpeningHours()
        for day_time in response.xpath('//*[contains(@class,"promo-banner__overlay-content")]//p//text()').getall()[
            -2:
        ]:
            item["opening_hours"].add_ranges_from_string(day_time)
        yield item
