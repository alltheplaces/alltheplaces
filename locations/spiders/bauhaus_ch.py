from typing import Iterable

from scrapy.http import Request, Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.hours import OpeningHours, DAYS_DE, CLOSED_DE
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


BAUHAUS_SHARED_ATTRIBUTES = {"brand": "Bauhaus", "brand_wikidata": "Q672043"}


class BauhausCHSpider(CrawlSpider):
    name = "bauhaus_ch"
    item_attributes = BAUHAUS_SHARED_ATTRIBUTES
    allowed_domains = ["www.bauhaus.ch", "goo.gl", "www.google.ch"]
    start_urls = ["https://www.bauhaus.ch/de/fachcentren"]
    rules = [Rule(LinkExtractor(allow=r"^https:\/\/www\.bauhaus\.ch\/de\/fachcentren\/fachcenter-[\w\-]+$"), "parse")]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,  # Don't check robots.txt for www.google.ch
        "DUPEFILTER_CLASS": "scrapy.dupefilters.BaseDupeFilter",  # Some stores have the same coordinates (source problem)
                                                                  # but it's better to extract duplicate coordinates via
                                                                  # the expanded www.google.ch URL than to ignore a store.
    }

    def parse(self, response: Response) -> Iterable[Request]:
        properties = {
            "ref": response.url.split("/fachcenter-", 1)[1],
            "branch": response.xpath('//main/section[1]/h1/text()').get().removeprefix("Fachcenter "),
            "addr_full": merge_address_lines(response.xpath('//main/section[3]//table/tbody/tr[1]/td[2]/text()').getall()),
            "phone": response.xpath('//main/section[3]//table/tbody/tr[2]/td[2]//text()').get(),
            "email": response.xpath('//main/section[3]//table/tbody/tr[3]/td[2]//text()').get(),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }

        hours_string = " ".join(response.xpath('//main/section[2]//table//text()').getall())
        properties["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_DE, closed=CLOSED_DE)

        apply_category(Categories.SHOP_DOITYOURSELF, properties)

        short_google_maps_url = response.xpath('//main/section[3]//a[contains(@href, "https://goo.gl/maps/")]/@href').get()
        item = Feature(**properties)
        item["extras"] = {}
        item["extras"]["@source_uri"] = item["website"]
        yield Request(url=short_google_maps_url, meta={"item": item}, callback=self.add_coordinates)

    # Follow shortened URL to find full Google Maps URL containing coordinates
    def add_coordinates(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        item["lat"], item["lon"] = url_to_coords(response.url)
        yield item
