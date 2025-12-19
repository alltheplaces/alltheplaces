from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS


class YhaGBSpider(SitemapSpider, CamoufoxSpider):
    name = "yha_gb"
    item_attributes = {"brand": "Youth Hostels Association", "brand_wikidata": "Q8059214"}
    allowed_domains = ["www.yha.org.uk"]
    sitemap_urls = ["https://www.yha.org.uk/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.yha\.org\.uk\/hostel\/yha-[\w\-]+", "parse")]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS | {"CAMOUFOX_MAX_PAGES_PER_CONTEXT": 1, "CAMOUFOX_MAX_CONTEXTS": 1}

    def parse(self, response: Response) -> Iterable[Feature]:
        properties = {
            "ref": response.url,
            "branch": response.xpath("//title/text()")
            .get()
            .split("|", 1)[0]
            .strip()
            .removeprefix("YHA ")
            .removesuffix(" Hostel"),
            "lat": response.xpath("//@data-lat").get(),
            "lon": response.xpath("//@data-lng").get(),
            "addr_full": merge_address_lines(response.xpath('//div[@class="map-overlay__section"]/a/text()').getall()),
            "phone": response.xpath('//dd/a[contains(@href, "tel:")]/@href').get(),
            "website": response.url,
        }
        apply_category(Categories.TOURISM_HOSTEL, properties)
        yield Feature(**properties)
