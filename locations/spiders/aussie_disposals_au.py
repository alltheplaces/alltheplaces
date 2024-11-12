import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class AussieDisposalsAUSpider(SitemapSpider):
    name = "aussie_disposals_au"
    item_attributes = {"brand": "Aussie Disposals", "brand_wikidata": "Q117847729"}
    sitemap_urls = ["https://www.aussiedisposals.com.au/pub/media/newsitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.aussiedisposals\.com\.au\/store-locator\/ad_", "parse")]
    allowed_domains = ["www.aussiedisposals.com.au"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = "AU"

    def parse(self, response: Response) -> Iterable[Feature]:
        # Note: AmastyStoreLocatorSpider not used here as opening hours are
        # not available through the embedded JavaScript blob this storefinder
        # extracts location information from.
        location_element = response.xpath('//div[@class="amlocator-location-container"]')
        properties = {
            "ref": response.url,
            "branch": location_element.xpath('.//h3/text()').get(),
            "addr_full": merge_address_lines(location_element.xpath('.//div[@class="amlocator-block-address"]//text()').getall()),
            "phone": location_element.xpath('.//div[@class="amlocator-block-phone"]//a[contains(@href, "tel:")]/@href').get("").replace("tel:", ""),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        properties["lat"], properties["lon"] = url_to_coords(location_element.xpath('//div[@class="directions-btn"]/a/@href').get())
        hours_text = re.sub(r"\s+", " ", " ".join(location_element.xpath('.//div[@class="amlocator-description-grey"]/div[1]/p//text()').getall())).strip()
        properties["opening_hours"].add_ranges_from_string(hours_text)
        yield Feature(**properties)
