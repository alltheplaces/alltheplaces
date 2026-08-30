from typing import Any, AsyncIterator, Iterable

from parsel import Selector
from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class SideStepSpider(Spider):
    name = "side_step"
    allowed_domains = ["www.side-step.co.za"]
    item_attributes = {"brand": "Side Step", "brand_wikidata": "Q116894527"}
    requires_proxy = "ZA"

    async def start(self) -> AsyncIterator[Request]:
        yield Request("https://www.side-step.co.za/amlocator/index/ajax/?p=1", callback=self.parse)

    def parse(self, response: Response, first_ref: int | None = None, **kwargs: Any) -> Iterable[Request]:
        locations = response.json()["items"]
        # Requesting a page past the last one silently serves the first page again.
        if locations[0]["id"] == first_ref:
            return

        for location in locations:
            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            item["branch"] = location["name"].removeprefix("Side Step ")
            store_url = Selector(text=location["popup_html"]).xpath("//a[@class='amlocator-link']/@href").get()
            yield response.follow(store_url, callback=self.parse_store, cb_kwargs={"item": item})

        page = int(response.url.rsplit("=", 1)[1])
        yield Request(
            f"https://www.side-step.co.za/amlocator/index/ajax/?p={page + 1}",
            callback=self.parse,
            cb_kwargs={"first_ref": first_ref or locations[0]["id"]},
        )

    def parse_store(self, response: Response, item: Feature) -> Iterable[Feature]:
        item["website"] = response.url
        item["addr_full"] = clean_address(
            response.xpath('//span[@class="amlocator-text -bold"]/../span').xpath("normalize-space(.)").getall()
        )
        item["phone"] = response.xpath(
            '//div[contains(@class, "amlocator-column")]//a[starts-with(@href, "tel:")]/@href'
        ).get()

        item["opening_hours"] = OpeningHours()
        for row in response.xpath('//div[@class="amlocator-week"]//div[contains(@class, "amlocator-row")]'):
            day = row.xpath('normalize-space(.//span[contains(@class, "-day")])').get()
            open_time, _, close_time = (
                row.xpath('normalize-space(.//span[contains(@class, "-time")])').get().partition(" - ")
            )
            item["opening_hours"].add_range(day, open_time, close_time)

        apply_category(Categories.SHOP_SHOES, item)
        yield item
