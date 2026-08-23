from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS_NL, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class InnoBESpider(CrawlSpider):
    name = "inno_be"
    item_attributes = {"brand": "Inno", "brand_wikidata": "Q300632"}
    allowed_domains = ["www.inno.be"]
    start_urls = ["https://www.inno.be/nl/stores"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    requires_proxy = "BE"
    rules = [Rule(LinkExtractor(r"^https:\/\/www\.inno\.be\/nl\/stores\/detail\?id=[\w\-]+$"), "parse")]

    def parse(self, response: Response) -> Iterable[Feature]:
        properties = {
            "ref": response.url,
            "branch": response.xpath('//h1[@class="store-detail__name"]/text()').get().removeprefix("INNO "),
            "addr_full": response.xpath('//h2[@class="store-detail__address"]/text()').get(),
            "phone": response.xpath('//a[contains(@class, "store-detail__phone")]/@href')
            .get()
            .removeprefix("tel:")
            .replace("/", "")
            .replace(".", ""),
            "email": response.xpath('//a[contains(@class, "store-detail__email")]/@href').get().removeprefix("mailto:"),
            "opening_hours": OpeningHours(),
        }
        apply_category(Categories.SHOP_DEPARTMENT_STORE, properties)
        hours_text = " ".join(response.xpath('//div[contains(@class, "js-store-hours")]//text()').getall())
        properties["opening_hours"].add_ranges_from_string(hours_text, days=DAYS_NL)
        extract_google_position(properties, response)
        if not properties.get("lat"):
            if lat := response.xpath("//@data-lat|//@data-latitude").get():
                properties["lat"] = float(lat)
                properties["lon"] = float(response.xpath("//@data-lng|//@data-longitude").get())
        yield Feature(**properties)
