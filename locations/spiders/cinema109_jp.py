from scrapy.http import Response, TextResponse

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class Cinema109JPSpider(StructuredDataSpider):
    name = "cinema109_jp"
    item_attributes = {"brand": "109シネマズ", "brand_wikidata": "Q10854269"}
    start_urls = ["https://109cinemas.net/"]
    wanted_types = ["MovieTheater"]

    def parse(self, response: TextResponse):
        theater_hrefs = response.xpath('//section[@id="theatres"]//a/@href').getall()
        for href in theater_hrefs:
            yield response.follow(href.rstrip("/") + "/access.html", callback=self.parse_sd)

    def post_process_item(self, item, response: Response, ld_data: dict):
        item["ref"] = item["website"].split("/")[-2]
        item["branch"] = item.pop("name", "").removeprefix("１０９シネマズ")
        item["name"] = None
        apply_category(Categories.CINEMA, item)
        yield item
