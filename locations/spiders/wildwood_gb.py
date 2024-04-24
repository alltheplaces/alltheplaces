from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import extract_email


class WildwoodGBSpider(SitemapSpider):
    name = "wildwood_gb"
    item_attributes = {"brand": "Wildwood", "brand_wikidata": "Q85300869"}
    sitemap_urls = ["https://wildwoodrestaurants.co.uk/restaurant-sitemap.xml"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        item["branch"] = response.xpath("//h1/text()").get().removeprefix("Wildwood ")
        item["addr_full"] = merge_address_lines(
            response.xpath('//div[@class="box box-grey box-address"]/div[@class="box-content"]/p[1]//text()').getall()
        )
        item["phone"] = response.xpath(
            '//div[@class="box box-grey box-address"]/div[@class="box-content"]/p[2]/text()'
        ).get()

        services = response.xpath(
            '//div[@class="box box-grey box-facilities"]//ul/li/span[@class="list-icon-text"]/text()'
        ).getall()

        apply_yes_no(Extras.BABY_CHANGING_TABLE, item, "Baby Changing" in services)
        apply_yes_no(Extras.WHEELCHAIR, item, "Disabled Access" in services)
        apply_yes_no(Extras.WIFI, item, "Free WiFi" in services)
        apply_yes_no(Extras.OUTDOOR_SEATING, item, "Outside Seating" in services)

        extract_email(item, response)

        yield item
