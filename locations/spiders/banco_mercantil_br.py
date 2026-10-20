from typing import Any, Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_PT, OpeningHours, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BancoMercantilBRSpider(SitemapSpider, StructuredDataSpider):
    name = "banco_mercantil_br"
    item_attributes = {"brand": "Banco Mercantil do Brasil", "brand_wikidata": "Q9645252"}
    sitemap_urls = ["https://encontre.bancomercantil.com.br/sitemap.xml"]
    sitemap_rules = [(r"/banco-mercantil(?:-\d+)?$", "parse_sd")]
    search_for_facebook = False

    def post_process_item(
        self, item: Feature, response: TextResponse, ld_data: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        item["ref"] = response.xpath("//@data-trackingclient-store_id").get()
        item["branch"] = item.pop("name").removeprefix("Banco Mercantil - ")
        item["phone"] = None
        item["opening_hours"] = self.parse_hours(response)
        if review_link := response.xpath('//a[contains(@href, "placeid=")]/@href').get():
            item["extras"]["ref:google:place_id"] = review_link.split("placeid=")[1].split("&")[0]
        apply_category(Categories.BANK, item)
        yield item

    @staticmethod
    def parse_hours(response: TextResponse) -> OpeningHours:
        oh = OpeningHours()
        for row in response.xpath('//dl[@class="b-week"]/dt'):
            day = sanitise_day(row.xpath("normalize-space(text())").get().split("-")[0], DAYS_PT)
            if not day:
                continue
            for time_range in row.xpath("following-sibling::dd[1]/span/text()").getall():
                time_range = time_range.strip()
                if time_range == "Fechado":
                    oh.set_closed(day)
                else:
                    open_time, _, close_time = time_range.partition("-")
                    oh.add_range(day, open_time, close_time)
        return oh
