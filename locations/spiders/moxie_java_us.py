from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class MoxieJavaUSSpider(Spider):
    name = "moxie_java_us"
    item_attributes = {"brand": "Moxie Java"}
    start_urls = ["https://moxiejava.com/locations/"]

    def parse(self, response):
        for card in response.css(".location_box"):
            address = card.css("p.kt-blocks-info-box-text")
            locality = address.xpath("./br[1]/following-sibling::text()[1]").get().strip()
            city, region = locality.rsplit(",", 1)
            state, postcode = region.strip().rsplit(" ", 1)
            website = response.urljoin(card.css("a::attr(href)").get()).rstrip("/") + "/"
            item = Feature(
                ref=website.rstrip("/").rsplit("/", 1)[-1],
                branch=card.css("h3::text").get().removeprefix("Moxie Java "),
                street_address="".join(
                    address.xpath("./br[1]/preceding-sibling::node()/descendant-or-self::text()").getall()
                ).strip(),
                city=city,
                state=state,
                postcode=postcode,
                country="US",
                phone=address.css("strong::text").get(),
                website=website,
            )
            apply_category(Categories.CAFE, item)
            yield response.follow(
                website,
                callback=self.parse_store,
                cb_kwargs={"item": item},
                meta={"handle_httpstatus_list": [404]},
            )

    def parse_store(self, response, item):
        # Several stores remain listed in the directory but have no detail page.
        if response.status == 404:
            item["website"] = self.start_urls[0]
            yield item
            return
        item["website"] = response.url
        # The Southside directory city is wrong; its detail page has a truncated postcode.
        locality = response.xpath("//h1/following-sibling::p[1]/br/following-sibling::text()[1]").get()
        if locality and "," in locality:
            item["city"] = locality.rsplit(",", 1)[0].strip()
        hours = OpeningHours()
        for row in response.css(".hours_table tr"):
            hours.add_ranges_from_string(" ".join(row.xpath(".//text()").getall()))
        item["opening_hours"] = hours
        yield item
