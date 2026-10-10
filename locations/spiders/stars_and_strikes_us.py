import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class StarsAndStrikesUSSpider(Spider):
    name = "stars_and_strikes_us"
    item_attributes = {"brand": "Stars and Strikes"}
    start_urls = ["https://starsandstrikes.com/our-locations/"]

    def parse(self, response):
        for location in response.css("div.special-clickable-card"):
            website = location.css("a.clickable-card-link::attr(href)").get()
            item = Feature(
                ref=website.rstrip("/").rsplit("/", 1)[-1],
                branch=location.css("h4::text").get(),
                street_address=" ".join(
                    [
                        location.css(".segment-street_number::text").get(),
                        location.css(".segment-street_name::text").get(),
                    ]
                ),
                city=location.css(".segment-city::text").get(),
                state=location.css(".segment-state::text").get(),
                postcode=location.css(".segment-post_code::text").get(),
                country="US",
                website=website,
            )
            apply_category(Categories.BOWLING, item)
            yield response.follow(website, callback=self.parse_location, cb_kwargs={"item": item})

    def parse_location(self, response, item):
        hours = OpeningHours()
        for row in response.css("table.hours__table tr"):
            text = " ".join(row.css("::text").getall())
            text = re.sub(r"\bNoon\b", "12pm", text, flags=re.I)
            text = re.sub(r"\bMidnight\b", "12am", text, flags=re.I)
            hours.add_ranges_from_string(text, days=DAYS_EN)
        item["opening_hours"] = hours
        yield item
