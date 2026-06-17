from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class MiladysZASpider(SitemapSpider):
    name = "miladys_za"
    sitemap_urls = ["https://www.miladys.com/media/sitemap.xml"]
    sitemap_rules = [(r"/miladys-[-\w]+-\d+$", "parse")]
    item_attributes = {
        "brand": "Miladys",
        "brand_wikidata": "Q116619751",
    }
    custom_settings = {"DOWNLOAD_TIMEOUT": 120}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.url.rsplit("-", 1)[-1]
        item["website"] = response.url
        item["branch"] = (
            response.xpath('.//h1[@class="page-title"]/span/text()')
            .get("")
            .replace(self.item_attributes["brand"], "")
            .strip()
        )
        address = response.xpath('.//div[@class="address-line"]')
        if not address:  # Not a valid location page
            return
        item["addr_full"] = clean_address(address.xpath("./text()").get())
        item["phone"] = response.xpath('.//div[contains(@class,"phone-number")]/div/text()').get()
        extract_google_position(item, response)

        item["opening_hours"] = self.parse_opening_hours(response)

        yield item

    def parse_opening_hours(self, response: Response) -> OpeningHours:
        opening_hours = OpeningHours()
        opening_hours.add_ranges_from_string(response.xpath('string(.//div[@class="shop-opening-times"])').get())
        # Some places have no opening hours (for some days) so mysteriously return the current time for open and close
        for day in DAYS:
            if day in opening_hours.days_closed:
                continue
            for h in sorted(opening_hours.day_hours[day]):
                if h[0] == h[1]:
                    opening_hours.day_hours[day].remove(h)
        return opening_hours
