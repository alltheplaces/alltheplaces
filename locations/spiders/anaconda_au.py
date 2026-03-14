from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.structured_data_spider import extract_phone


class AnacondaAUSpider(SitemapSpider):
    name = "anaconda_au"
    item_attributes = {"brand": "Anaconda", "brand_wikidata": "Q105981238"}
    sitemap_urls = ["https://www.anacondastores.com/sitemap/store/store-sitemap.xml"]
    sitemap_rules = [(r"/store/[-\w]+/[-\w]+/[-\w]+$", "parse")]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        # The server redirects with http 302 and then redirects again back to the original URL, which Scrapy considers as a duplicate request by default.
        "DUPEFILTER_CLASS": "scrapy.dupefilters.BaseDupeFilter",
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        properties = {
            "ref": response.xpath('//div[contains(@id, "maps_canvas")]/@data-storeid').extract_first(),
            "branch": response.xpath('//div[contains(@id, "maps_canvas")]/@data-storename')
            .extract_first()
            .removeprefix("Anaconda "),
            "lat": response.xpath('//div[contains(@id, "maps_canvas")]/@data-latitude').extract_first(),
            "lon": response.xpath('//div[contains(@id, "maps_canvas")]/@data-longitude').extract_first(),
            "addr_full": clean_address(
                response.xpath('//div[contains(@class, "store-detail-desc")]//li/text()').extract()
            ),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        extract_phone(properties, response)

        for rule in response.xpath('//*[contains(text(),"Opening Hours")]/parent::div//table/tbody/tr'):
            if day := sanitise_day(rule.xpath("./td[1]/text()").extract_first()):
                hours = rule.xpath("./td[2]/text()").extract_first()
                if "Closed" in hours.title():
                    properties["opening_hours"].set_closed(day)
                else:
                    properties["opening_hours"].add_ranges_from_string(f"{day} {hours}")

        yield Feature(**properties)
