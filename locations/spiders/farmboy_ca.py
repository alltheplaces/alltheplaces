from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class FarmboyCASpider(SitemapSpider):
    name = "farmboy_ca"
    item_attributes = {"brand": "Farmboy", "brand_wikidata": "Q5435469"}
    allowed_domains = ["www.farmboy.ca"]
    sitemap_urls = ["https://www.farmboy.ca/stores-sitemap.xml"]
    sitemap_rules = [(r"/stores/[-\w]+", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath("//title/text()").get("").split("|")[0].removeprefix("Farm Boy ").strip()
        item["addr_full"] = response.xpath('//*[@class="address"]/text()').get()
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        if contact_details := response.xpath('//*[@class="connect"]/text()').getall():
            if "Fax" in contact_details[-1]:
                item["extras"]["fax"] = contact_details[-1]
        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//*[contains(@class,"store-store-hours")]//li'):
            item["opening_hours"].add_ranges_from_string(
                f"{rule.xpath('./span[1]//text()').get()} {rule.xpath('./span[2]//text()').get()}"
            )
        yield item
