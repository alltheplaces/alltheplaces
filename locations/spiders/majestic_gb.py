from typing import Any, Iterable

from scrapy.http import Request, Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class MajesticGBSpider(CrawlSpider):
    name = "majestic_gb"
    item_attributes = {"brand": "Majestic", "brand_wikidata": "Q6737725"}
    start_urls = ["https://www.majestic.co.uk/stores"]
    rules = [Rule(LinkExtractor(allow="/stores/"), callback="parse")]
    allowed_domains = ["www.majestic.co.uk"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "Host": "www.majestic.co.uk",
            "DNT": "1",
        },
        "USER_AGENT": BROWSER_DEFAULT,
    }
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//li[contains(@class, "store-item")]'):
            item = Feature()
            item["ref"] = item["website"] = response.urljoin(location.xpath(".//@data-id").get())
            item["addr_full"] = response.xpath('//p[@class="store__address"]/text()').get()
            item["lat"] = location.xpath(".//@data-lat").get()
            item["lon"] = location.xpath(".//@data-long").get()
            item["name"] = location.xpath(".//@data-name").get()
            item["branch"] = item.pop("name").removeprefix("Majestic ")
            item["phone"] = location.xpath(".//@data-phone").get()
            item["image"] = location.xpath('./span[@class="store-list-image"]/img/@src').get()
            apply_category(Categories.SHOP_WINE, item)

            yield Request(url=item["website"], meta={"item": item}, callback=self.parse_details)

    def parse_details(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        item["addr_full"] = response.xpath('//p[@class="store__address"]/text()').get()
        item["facebook"] = response.xpath('//a[contains(@href, "facebook.com/pages/")]/@href').get()
        item["email"] = response.xpath('//*[@id = "clickEmail"]/text()').get()
        hours_string = " ".join(response.xpath('//div[contains(@class, "store-time-line")]//text()').getall())
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
