from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature


class RaSushiUSSpider(SitemapSpider):
    name = "ra_sushi_us"
    item_attributes = {"brand": "RA Sushi", "brand_wikidata": "Q117400401"}
    sitemap_urls = ["https://rasushi.com/stores-sitemap.xml"]
    sitemap_rules = [("/locations/(?!$)", "parse_store")]
    custom_settings = {"REDIRECT_ENABLED": "False"}

    def parse_store(self, response):
        properties = {
            "ref": response.url.split("/")[-2],
            "name": response.xpath('//h1[contains(@class, "title")]/text()').get().strip(),
            "lat": response.xpath("//@data-lat").get(),
            "lon": response.xpath("//@data-lng").get(),
            "addr_full": " ".join(
                filter(
                    None,
                    response.xpath(
                        "//div[contains(@class, 'store_locator_single_address') or contains(@class, 'address')]/text()"
                    ).getall(),
                )
            ).strip(),
            "phone": response.xpath('//div[contains(@class, "phone")]/a/text()').get(),
            "website": response.url,
        }
        restaurant = response.xpath('//span[contains(@class, "devOp1")]/text()').get().strip() == "Restaurant"
        apply_yes_no(Extras.INDOOR_SEATING, properties, restaurant, False)
        apply_yes_no(Extras.DELIVERY, properties, True)
        apply_yes_no(Extras.TAKEAWAY, properties, restaurant, False)
        properties["opening_hours"] = OpeningHours()
        if restaurant:
            hours_string = (
                " ".join(
                    filter(
                        None,
                        response.xpath('//section[contains(@class, "hours_wrapper")]//ul/li[1]//p/text()').getall(),
                    )
                )
                .strip()
                .upper()
                .replace("MIDNIGHT", "12:00AM")
            )
            properties["opening_hours"].add_ranges_from_string(hours_string)
        yield Feature(**properties)
