from typing import Iterable

from scrapy.http import JsonRequest, Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours, DAYS_EN
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class HopdoddyBurgerBarUSSpider(SitemapSpider, StructuredDataSpider):
    name = "hopdoddy_burger_bar_us"
    item_attributes = {"brand": "Hopdoddy Burger Bar", "brand_wikidata": "Q123689179"}
    sitemap_urls = ["https://www.hopdoddy.com/robots.txt"]
    sitemap_rules = [("/locations/", "parse")]
    wanted_types = ["FoodEstablishment"]
    time_format = "%I %p"

    def sitemap_filter(self, entries):
        for entry in entries:
            # Avoid unwanted 301 redirects
            entry["loc"] = entry["loc"].replace("https://hopdoddy.com/", "https://www.hopdoddy.com/")
            yield entry

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[JsonRequest]:
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath('//h1[@class="lt__locationname"]/text()').get()
        item.pop("image", None)
        item.pop("facebook", None)
        extract_google_position(item, response)
        apply_category(Categories.FAST_FOOD, item)

        olo_id = response.xpath('//@data-location-olo-id').get()
        cloudfront_id = response.xpath('//script[contains(@src, ".cloudfront.net/index.js")]/@src').get().removeprefix("https://").removesuffix(".cloudfront.net/index.js")
        opening_hours_url = f"https://{cloudfront_id}.cloudfront.net/calendars/{olo_id}"
        yield JsonRequest(url=opening_hours_url, meta={"item": item}, callback=self.parse_opening_hours)

    def parse_opening_hours(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        item["extras"]["@source_uri"] = ";".join([item["website"], response.url])
        item["opening_hours"] = OpeningHours()
        for day_hours in response.json()["data"]:
            item["opening_hours"].add_range(DAYS_EN[day_hours["day"]], day_hours["opens"], day_hours["closes"], "%I:%M%p")
        yield item
