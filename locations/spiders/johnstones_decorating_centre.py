from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class JohnstonesDecoratingCentreSpider(SitemapSpider):
    name = "johnstones_decorating_centre"
    item_attributes = {"brand": "Johnstone's Decorating Centre", "brand_wikidata": "Q121742106"}
    sitemap_urls = ["https://www.johnstonesdc.com/sitemap.xml"]

    # https://www.johnstonesdc.com/united-kingdom-region-norwich-17634
    # https://www.johnstonesdc.com/republic-of-ireland-region-dublin-rathmines-17621
    sitemap_rules = [(r"/(united-kingdom-region|republic-of-ireland-region)-[-\w]+\d+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if "https://www.johnstonesdc.com/stores" in response.url:
            return
        store_locator = response.xpath("//section[contains(@class, 'store-locator')]")
        address = store_locator.xpath(".//div[contains(@class, 'card-address')]/div/div/div/text()").getall()
        hours = store_locator.xpath(
            ".//div[contains(@class, 'card-opening-hours')]//div[contains(@class, 'info-details')]/span/text()"
        )

        contact = store_locator.xpath(
            ".//div[contains(@class, 'card-contact')]//div[contains(@class, 'info-details')]/span/text()"
        ).getall()
        map = store_locator.xpath(".//*[@id='map']")

        oh = OpeningHours()
        oh.add_ranges_from_string(" ".join(hours.getall()))

        properties = {
            "lat": map.xpath("@data-lat").get(0),
            "lon": map.xpath("@data-lng").get(0),
            "ref": response.url,
            "website": response.url,
            "opening_hours": oh,
            "addr_full": clean_address([address[1], address[2]]),
            "phone": contact[0],
            "email": contact[1],
            "name": address[0],
        }

        yield Feature(**properties)
