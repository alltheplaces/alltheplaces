from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import CLOSED_IT, DAYS_IT, OpeningHours
from locations.items import Feature


class SigmaITSpider(SitemapSpider):
    name = "sigma_it"
    item_attributes = {"brand": "Sigma", "brand_wikidata": "Q3977979"}
    sitemap_urls = ["https://www.supersigma.com/store-sitemap.xml"]
    sitemap_rules = [("/pdv/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["name"] = response.xpath("//title/text()").get()
        item["street_address"] = response.xpath('//*[@class="fl fw fs16 "]/text()').get()
        address2 = response.xpath('//*[@class="fl fw fs16 ml10 mt0 mb2"]').get()
        if address2:
            item["addr_full"] = ",".join([item["street_address"], address2])
        item["ref"] = item["website"] = response.url
        item["phone"] = response.xpath('//*[@class="fl fw fs16 "][2]/text()').get()
        item["email"] = response.xpath('//*[@class="fl fw fs14 mb3 "]/text()').get()
        extract_google_position(item, response)
        apply_category(Categories.SHOP_SUPERMARKET, item)
        hours_string = " ".join(
            filter(
                None, map(str.strip, response.xpath('//span[contains(@class, "bkg_orari")]/span/span//text()').getall())
            )
        )
        if hours_string:
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_IT, closed=CLOSED_IT)
        yield item
