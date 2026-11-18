import json
from typing import Any
from urllib.parse import unquote

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class PharmaChoiceCASpider(SitemapSpider):
    name = "pharma_choice_ca"
    item_attributes = {"brand": "PharmaChoice", "brand_wikidata": "Q7180716"}
    sitemap_urls = ["https://www.pharmachoice.com/sitemap_index.xml"]
    sitemap_follow = ["location-sitemap"]
    sitemap_rules = [(r"/locations/([^/]+)/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.xpath('//*[@class="pcc-location-map"]/@data-location').get()
        if not data:
            return
        item = DictParser.parse(json.loads(data))
        item["ref"] = item["website"] = response.url
        item["branch"] = item.pop("name")
        if phone := response.xpath('//a[starts-with(@href, "tel:")]/@href').get():
            item["phone"] = unquote(phone.removeprefix("tel:"))
        apply_category(Categories.PHARMACY, item)

        if post_id := response.xpath('//*[@class="pcc-location-hours"]/@data-post-id').get():
            yield Request(
                f"https://www.pharmachoice.com/wp-json/pcc-widgets/v1/location/{post_id}?lang=en",
                callback=self.parse_hours,
                cb_kwargs={"item": item},
            )
        else:
            yield item

    def parse_hours(self, response: Response, item: Feature, **kwargs: Any) -> Any:
        item["opening_hours"] = oh = OpeningHours()
        for day, rule in ((response.json().get("store_hours") or {}).get("schedule") or {}).items():
            if rule["status"] == "open":
                oh.add_range(day, rule["open"], rule["close"])
            elif rule["status"] == "closed":
                oh.set_closed(day)
        yield item
