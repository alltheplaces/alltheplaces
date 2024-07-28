from copy import deepcopy

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class RednersUSSpider(SitemapSpider):
    name = "redners_us"
    item_attributes = {"brand": "Redner's", "brand_wikidata": "Q7306166"}
    allowed_domains = ["www.rednersmarkets.com"]
    sitemap_urls = ["https://www.rednersmarkets.com/ldm_map_location-sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.rednersmarkets\.com\/store-locations\/[a-zA-Z0-9\-]+(?:\.html)?$", "parse")]

    def parse(self, response):
        init_map_js = response.xpath('//script[contains(text(), "function initMap() {")]/text()').get()
        properties = {
            "ref": response.url,
            "name": response.xpath(
                '//article[contains(@class, "ldm_map_location")]//h1[contains(@class, "entry-title")]/text()'
            ).get(),
            "lat": init_map_js.split("lat: ", 1)[1].split(",", 1)[0].strip(),
            "lon": init_map_js.split("lng: ", 1)[1].split("}", 1)[0].strip(),
            "addr_full": clean_address(
                response.xpath(
                    '//article[contains(@class, "ldm_map_location")]//div[contains(@class, "entry-content")]/p[position() <= 2]//text()'
                ).getall()
            ),
            "phone": " ".join(
                response.xpath(
                    '//article[contains(@class, "ldm_map_location")]//div[contains(@class, "entry-content")]/p[last() - 2]/text()'
                ).getall()
            ).strip(),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }

        hours_string = (
            "Mo-Su: "
            + " ".join(
                response.xpath(
                    '//article[contains(@class, "ldm_map_location")]//div[contains(@class, "entry-content")]/p[last() - 1]/text()'
                ).getall()
            ).strip()
        )
        if "24 HOURS" in hours_string.upper():
            properties["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
        else:
            properties["opening_hours"].add_ranges_from_string(hours_string)

        if "gas-station" in response.url or "quick-shoppe" in response.url:
            properties["brand"] = "Redner's Quick Shoppe"
            properties["brand_wikidata"] = "Q125102841"
            convenience_store = deepcopy(properties)
            convenience_store["ref"] = convenience_store["ref"] + "#convenience"
            apply_category(Categories.SHOP_CONVENIENCE, convenience_store)
            yield Feature(**convenience_store)
            properties["ref"] = properties["ref"] + "#fuel"
            apply_category(Categories.FUEL_STATION, properties)
        else:
            apply_category(Categories.SHOP_SUPERMARKET, properties)

        yield Feature(**properties)
