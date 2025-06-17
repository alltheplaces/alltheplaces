from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class DollarGeneralSpider(SitemapSpider):
    name = "dollar_general"
    item_attributes = {
        "brand": "Dollar General",
        "brand_wikidata": "Q145168",
        "country": "US",
    }
    allowed_domains = ["dollargeneral.com"]
    sitemap_urls = ["https://www.dollargeneral.com/sitemap-main.xml"]
    sitemap_rules = [(r"https:\/\/www\.dollargeneral\.com\/store-directory\/\w{2}\/.*\/\d+$", "parse")]
    handle_httpstatus_list = [401]  # The server responds with HTTP 401, but the page content is still returned.

    def parse(self, response: Response, **kwargs: Any) -> Any:
        properties = {
            "street_address": response.xpath("//@data-address").extract_first(),
            "city": response.xpath("//div[@data-city]/@data-city").extract_first(),
            "state": response.xpath("//div[@data-state]/@data-state").extract_first(),
            "postcode": response.xpath("//div[@data-zip]/@data-zip").extract_first(),
            "lat": response.xpath("//div[@data-latitude]/@data-latitude").extract_first(),
            "lon": response.xpath("//div[@data-longitude]/@data-longitude").extract_first(),
            "phone": response.xpath("//div[@data-phone]/@data-phone").extract_first(),
            "website": response.url,
            "ref": response.url.rsplit("/", 1)[-1].rsplit(".")[0],
            "name": self.item_attributes["brand"],
        }

        oh = OpeningHours()
        for d in DAYS_FULL:
            hours = response.xpath(f"//@data-{d.lower()}").get()
            if not hours:
                continue
            oh.add_ranges_from_string(f"{d} {hours}")

        properties["opening_hours"] = oh

        apply_category(Categories.SHOP_VARIETY_STORE, properties)

        yield Feature(**properties)
