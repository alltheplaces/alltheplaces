from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class UnionSavingsBankSpider(SitemapSpider):
    name = "union_savings_bank"
    item_attributes = {"brand": "Union Savings Bank", "brand_wikidata": "Q69206498", "extras": Categories.BANK.value}
    allowed_domains = ["usavingsbank.com"]
    sitemap_urls = ["https://usavingsbank.com/branches-sitemap.xml"]

    def parse(self, response):
        if 302 in response.meta.get("redirect_reasons", ()):
            # 'Coming soon' redirects to location index
            return

        oh = OpeningHours()
        for hours in response.css(".hours"):
            day, interval = hours.xpath(".//div/text()").extract()
            if interval == "Closed":
                continue
            open_time, close_time = interval.split("-")
            oh.add_range(day[:2], open_time, close_time, "%I%p")
        city_state_postcode = response.css("#address_c .city_state_zip::text").get()
        city_state, postcode = city_state_postcode.rsplit(" ", 1)
        city, state = city_state.rsplit(", ", 1)
        properties = {
            "ref": list(filter(None, response.url.split("/")))[-1],
            "website": response.url,
            "name": response.css("#address_c h4::text").get(),
            "opening_hours": oh.as_opening_hours(),
            "phone": response.css(".contact_numbers_c a::text").get(),
            "street_address": response.css("#address_c .address::text").get(),
            "city": city,
            "state": state,
            "postcode": postcode,
            "country": "US",
        }
        extract_google_position(properties, response)
        yield Feature(**properties)
