import html
import re
import unicodedata

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class HarrisScarfeAUSpider(SitemapSpider):
    name = "harris_scarfe_au"
    item_attributes = {"brand": "Harris Scarfe", "brand_wikidata": "Q5665029"}
    sitemap_urls = ["https://www.harrisscarfe.com.au/sitemap/store/store-sitemap.xml?queueittoken=e_harrisscarfe~ts_1734950356~ce_true~rt_safetynet~h_03afd3fd079b81a4185484a4329694c58554f14cefb91dd5a1ae291868e652e4"]
    sitemap_rules = [(r"^https://www\.harrisscarfe\.com\.au/store/(?!online)[^/]+/[^/]+/\d+$", "parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        properties = {
            "ref": response.xpath('//div[@id="maps_canvas"]/@data-storeid').get(),
            "name": response.xpath('//div[@id="maps_canvas"]/@data-storename').get(),
            "lat": response.xpath('//div[@id="maps_canvas"]/@data-latitude').get(),
            "lon": response.xpath('//div[@id="maps_canvas"]/@data-longitude').get(),
            "addr_full": re.sub(
                r"\s{2,}",
                " ",
                unicodedata.normalize(
                    "NFKD",
                    html.unescape(
                        " ".join(
                            response.xpath('//div[contains(@class, "store-detail-desc")]/ul[1]/li/text()').getall()
                        )
                    ),
                )
                .replace("\n", " ")
                .strip(),
            ),
            "phone": response.xpath('//a[contains(@href, "tel:")]/text()').get().strip(),
            "website": response.url,
        }
        hours_string = " ".join(
            filter(None, response.xpath('//div[contains(@class, "store-detail")]/div[2]//table//td/text()').getall())
        )
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string)
        yield Feature(**properties)
