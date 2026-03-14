from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.outdoor_supply_hardware_us import decode_email


class FrankieAndBennysGBSpider(SitemapSpider):
    name = "frankie_and_bennys_gb"
    item_attributes = {"brand": "Frankie & Benny's", "brand_wikidata": "Q5490892"}
    sitemap_urls = ["https://www.frankieandbennys.com/sitemap.xml"]
    sitemap_rules = [(r"/restaurants/[-\w]+", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        extract_google_position(item, response)
        item["ref"] = item["website"] = response.url
        item["addr_full"] = response.xpath('//*[@class="address"]/text()').get()
        item["phone"] = response.xpath('//*[contains(@href, "tel:")]/@href').get()
        item["email"] = decode_email(response.xpath("//@data-cfemail").get(""))
        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//*[@class="opening-hours-day"]'):
            if day := rule.xpath("./span[1]/text()").get():
                item["opening_hours"].add_ranges_from_string(f"{day}: {rule.xpath('./span[2]/text()').get()}")

        yield from self.parse_item(item, response) or []

    def parse_item(self, item: Feature, response: Response, **kwargs) -> Iterable[Feature]:
        item["branch"] = response.xpath('//*[@class="d-block gamay-extra-bold"]/text()').get()
        facilities = response.xpath('//*[@class="facility-name"]/text()').getall()
        apply_yes_no(Extras.WHEELCHAIR, item, "Wheelchair Access" in facilities)
        apply_yes_no(Extras.OUTDOOR_SEATING, item, "Outdoor Seating" in facilities)
        apply_yes_no(Extras.BABY_CHANGING_TABLE, item, "Baby Changing" in facilities)
        apply_yes_no(Extras.WIFI, item, "Wi-Fi" in facilities)
        yield item
