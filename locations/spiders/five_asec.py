from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import CLOSED_FR, DAYS_FR, OpeningHours
from locations.items import Feature


class FiveAsecSpider(SitemapSpider):
    name = "five_asec"
    item_attributes = {"brand": "5àsec", "brand_wikidata": "Q2817899"}
    sitemap_urls = ["https://www.5asec.fr/sitemap_index.xml"]
    sitemap_follow = ["store"]
    sitemap_rules = [(r"fr/fr/magasin/[-\w]+", "parse")]
    skip_auto_cc_domain = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.xpath("//@data-store-id").get()
        item["website"] = response.url
        item["addr_full"] = response.xpath('string(//a[@class="address"]/span)').get().strip()
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        item["phone"] = response.xpath('//a[@class="store-phone"]/@href').get()
        item["opening_hours"] = self.parse_opening_hours(response)
        yield item

    def parse_opening_hours(self, response: Response) -> OpeningHours:
        opening_hours = OpeningHours()
        for rule in response.xpath('//*[@class="store-opening-hours"]//li/text()').getall():
            opening_hours.add_ranges_from_string(rule, days=DAYS_FR, closed=CLOSED_FR)
        return opening_hours
