import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature


class CharlesClinkardGBSpider(CrawlSpider):
    name = "charles_clinkard_gb"
    item_attributes = {"brand": "Charles Clinkard", "brand_wikidata": "Q134454710"}
    allowed_domains = ["www.charlesclinkard.co.uk"]
    start_urls = ["https://www.charlesclinkard.co.uk/map"]
    rules = [Rule(LinkExtractor(allow=r"/map/[^/]+$"), "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        map_data = response.xpath('//script[contains(text(), "google.maps.LatLng")]/text()').extract_first()
        coordinates = re.search(r"var myLatlng = new google\.maps\.LatLng\((.*)\)", map_data).group(1)
        lat, lon = coordinates.split(",")

        properties = {
            "branch": response.xpath("//h1/text()").extract_first(),
            "addr_full": ", ".join(
                response.xpath('//div[@class="col l-col-16 store-locator__store__col"]/div/p/span/text()').extract()
            ),
            "phone": response.xpath(
                '//div[@class="col l-col-16 store-locator__store__col"]/div/span/a[contains(@href, "tel:")]/text()'
            ).extract_first(),
            "ref": response.url.replace("https://www.charlesclinkard.co.uk/map/", ""),
            "website": response.url,
            "lat": lat,
            "lon": lon,
        }

        apply_category(Categories.SHOP_SHOES, properties)

        yield Feature(**properties)
