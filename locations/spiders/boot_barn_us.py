from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class BootBarnUSSpider(SitemapSpider):
    name = "boot_barn_us"
    item_attributes = {"brand": "Boot Barn", "brand_wikidata": "Q109825187"}
    allowed_domains = ["www.bootbarn.com"]
    sitemap_urls = ["https://www.bootbarn.com/sitemap-store-sitemap.xml"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_DELAY": 3, "CONCURRENT_REQUESTS": 1}
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath('//*[@class="section-title"]/text()').get().replace(" Store", "")
        item["street_address"] = response.xpath('//*[@class="store-address1"]/text()').get()
        item["city"] = response.xpath('//*[@class="store-address-city"]/text()').get()
        item["state"] = response.xpath('//*[@class="store-address-state"]/text()').get()
        item["postcode"] = response.xpath('//*[@class="store-address-postal-code"]/text()').get()
        item["phone"] = response.xpath('//*[@class="store-phone"]/text()').get()
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lon").get()
        item["ref"] = item["website"] = response.url
        oh = OpeningHours()
        container = response.css(".store-hours-container .store-hours-days")
        if not container:
            self.logger.warning("Hours container not found on %s", response.url)
            return

        for day_span in container.css("span.stores-day"):

            day = day_span.xpath("normalize-space(text())").get().replace(":", "")

            time = " ".join(day_span.xpath("following-sibling::span[1]").xpath("normalize-space(.)").get().split())
            open_time, close_time = time.split(" - ")
            oh.add_range(day, open_time.strip(), close_time.strip(), "%I:%M%p")
            item["opening_hours"] = oh

        yield item
