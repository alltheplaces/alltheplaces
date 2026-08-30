from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class MenchiesSpider(SitemapSpider):
    name = "menchies"
    item_attributes = {"brand": "Menchie's", "brand_wikidata": "Q6816528"}
    sitemap_urls = ["https://www.menchies.com/location-sitemap.xml"]
    sitemap_rules = [(r"/location/[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        branch = response.xpath('//main[@id="single-location"]//h1/text()').get("")
        if "coming soon" in branch.lower():
            return
        location = response.xpath('//div[@class="sl-heading-meta"]')
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = branch.strip()
        item["addr_full"] = location.xpath('.//div[contains(@class, "address-col")]//p/text()').get()
        item["phone"] = location.xpath('.//a[starts-with(@href, "tel:")]/@href').get("").removeprefix("tel:")
        item["facebook"] = location.xpath('.//a[contains(@href, "facebook.com")]/@href').get()
        item["twitter"] = location.xpath(
            './/a[contains(@href, "twitter.com") or contains(@href, "//x.com")]/@href'
        ).get()
        for key in ["facebook", "twitter"]:
            if item[key] and ("mymenchies" in item[key].lower() or "menchies-frozen-yogurt" in item[key].lower()):
                item[key] = None
        item["opening_hours"] = OpeningHours()
        for rule in location.xpath('.//div[contains(@class, "hours-col")]//p/text()').getall():
            item["opening_hours"].add_ranges_from_string(rule)
        extract_google_position(item, location)
        apply_category(Categories.ICE_CREAM, item)
        yield item
