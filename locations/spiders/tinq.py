from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class TinqSpider(SitemapSpider):
    name = "tinq"
    item_attributes = {"brand": "TinQ", "brand_wikidata": "Q2132028"}
    sitemap_urls = ["https://www.tinq.nl/sitemap.xml", "https://www.tinq.be/sitemap.xml"]
    sitemap_rules = [("/tankstations/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        item["street_address"] = clean_address(
            [
                response.xpath('//*[@class="address-line1"]/text()').get(),
                response.xpath('//*[@class="address-line2"]/text()').get(),
            ]
        )
        item["postcode"] = response.xpath('//*[@class="postal-code"]/text()').get()
        item["city"] = response.xpath('//*[@class="locality"]/text()').get()
        item["country"] = response.xpath('//*[@class="country"]/text()').get()
        apply_category(Categories.FUEL_STATION, item)
        fuels = [
            f.strip() for f in response.xpath('//*[contains(@class,"name-taxonomy-term-title")]/p/text()').getall()
        ]
        apply_yes_no(Fuel.ADBLUE, item, any("AdBlue" in fuel for fuel in fuels))
        apply_yes_no(Fuel.BIODIESEL, item, any("HVO100" in fuel for fuel in fuels))
        apply_yes_no(Fuel.DIESEL, item, any("Diesel B7" in fuel for fuel in fuels))
        apply_yes_no(Fuel.HGV_DIESEL, item, any("Truck Diesel" in fuel for fuel in fuels))
        apply_yes_no(Fuel.E10, item, any("Euro95 E10" in fuel for fuel in fuels))
        apply_yes_no(Fuel.LPG, item, any("LPG" in fuel for fuel in fuels))
        apply_yes_no(
            Fuel.OCTANE_98,
            item,
            any("Superplus 98 E5" in fuel.replace("Superplus98 E5", "Superplus 98 E5") for fuel in fuels),
        )
        yield item
