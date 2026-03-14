import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature


class RoyalLepageSpider(CrawlSpider):
    name = "royal_lepage"
    item_attributes = {"brand": "Royal LePage", "brand_wikidata": "Q7374385"}
    allowed_domains = ["royallepage.ca"]
    start_urls = [
        "https://www.royallepage.ca/en/search/offices/?lat=&lng=&address=&designations=&address_type=&city_name=&prov_code=&sortby=&transactionType=OFFICE&name=&location=&language=&specialization=All"
    ]
    rules = [
        Rule(LinkExtractor(allow="/office/", restrict_xpaths="//address"), callback="parse"),
        Rule(
            LinkExtractor(allow=r"/offices/\d+/", restrict_xpaths='//*[contains(@class, "paginator__pages")]'),
        ),
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        map_script = response.xpath('//script/text()[contains(., "staticMap")]').get()
        lat = re.search("latitude: (.*?),?$", map_script, flags=re.M).group(1)
        lon = re.search("longitude: (.*?),?$", map_script, flags=re.M).group(1)

        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": response.xpath('normalize-space(//*[@itemprop="name"]//text())').extract_first().strip(" *"),
            "addr_full": response.xpath('normalize-space(//*[@itemprop="address"]/p/text())').extract_first(),
            "country": "CA",
            "phone": response.xpath('normalize-space(//a[@itemprop="telephone"]//text())').extract_first(),
            "website": response.url,
            "lat": float(lat) if lat else None,
            "lon": float(lon) if lon else None,
        }

        yield Feature(**properties)
