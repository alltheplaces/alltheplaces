from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class EastOfEnglandCoopGBSpider(SitemapSpider):
    name = "east_of_england_coop_gb"
    EAST_OF_ENGLAND_COOP = {"brand": "East of England CO-OP", "brand_wikidata": "Q5329759"}
    COOP_DAILY = {"brand": "Co-op Daily", "brand_wikidata": "Q107589681"}
    sitemap_urls = ["https://www.eastofengland.coop/sitemap.xml"]
    sitemap_rules = [("/store/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath("//h2/text()").get()
        item["street_address"] = response.xpath('//*[@class="flex flex-col gap-1"]/span/text()').get()
        item["city"] = response.xpath('//*[@class="flex flex-col gap-1"]/span[2]/text()').get()
        item["postcode"] = response.xpath('//*[@class="flex flex-col gap-1"]/span[3]/text()').get()
        item["phone"] = response.xpath('//*[contains(@href, "tel:")]/text()').get()
        item["ref"] = item["website"] = response.url

        extract_google_position(item, response)

        if "post-office" in response.url:
            apply_category(Categories.POST_OFFICE, item)
        elif "food" in response.url:
            if item["branch"].endswith(" Supermarket"):
                item.update(self.EAST_OF_ENGLAND_COOP)
                apply_category(Categories.SHOP_SUPERMARKET, item)
            else:
                item.update(self.COOP_DAILY)
                apply_category(Categories.SHOP_CONVENIENCE, item)
        elif "travel" in response.url:
            item["name"] = "CO-OP Travel"
            item.update(self.EAST_OF_ENGLAND_COOP)
            apply_category(Categories.SHOP_TRAVEL_AGENCY, item)
        elif "funerals" in response.url:
            item["name"] = "East of England CO-OP Funeral Services"
            item.update(self.EAST_OF_ENGLAND_COOP)
            apply_category(Categories.SHOP_FUNERAL_DIRECTORS, item)

        oh = OpeningHours()
        for day_time in response.xpath('//*[@class="flex flex-col items-center gap-1.5"]//li'):
            day = day_time.xpath(".//span[1]/text()").get()
            time = day_time.xpath(".//span[2]").xpath("normalize-space()").get()
            if time == "Closed":
                oh.set_closed(day)
            else:
                open_time, close_time = time.split(" - ")
                oh.add_range(day=day, open_time=open_time, close_time=close_time)
        item["opening_hours"] = oh

        yield item
