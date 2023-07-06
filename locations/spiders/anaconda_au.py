from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import extract_phone


class AnacondaAUSpider(SitemapSpider):
    name = "anaconda_au"
    item_attributes = {"brand": "Anaconda", "brand_wikidata": "Q105981238"}
    allowed_domains = ["www.anacondastores.com"]
    sitemap_urls = ["https://www.anacondastores.com/sitemap/store/store-sitemap.xml"]
    sitemap_rules = [
        (
            r"^https://www.anacondastores.com/store/(?:queensland|new-south-wales|victoria|tasmania|western-australia|south-australia|northern-territory|australian-capital-territory)/[\w\-]+/a\d{3}$",
            "parse_store",
        )
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_store(self, response):
        properties = {
            "ref": response.xpath('//div[contains(@id, "maps_canvas")]/@data-storeid').extract_first(),
            "name": response.xpath('//div[contains(@id, "maps_canvas")]/@data-storename').extract_first(),
            "lat": response.xpath('//div[contains(@id, "maps_canvas")]/@data-latitude').extract_first(),
            "lon": response.xpath('//div[contains(@id, "maps_canvas")]/@data-longitude').extract_first(),
            "addr_full": " ".join(
                " ".join(response.xpath('//div[contains(@class, "store-detail-desc")]/ul/li/text()').extract()).split()
            ),
            "country": "AU",
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        extract_phone(properties, response)
        hours_raw = (
            " ".join(
                response.xpath(
                    '//div[contains(@class,"store-detail")]/div[2]/div[2]/div/table/tbody/tr/td/text()'
                ).extract()
            )
            .replace("Closed", "0:00am to 0:00am")
            .replace("to", "")
            .split()
        )
        hours_raw = [hours_raw[n : n + 3] for n in range(0, len(hours_raw), 3)]
        for day in hours_raw:
            if day[1] == "0:00am" and day[2] == "0:00am":
                continue
            properties["opening_hours"].add_range(DAYS_EN[day[0]], day[1].upper(), day[2].upper(), "%I:%M%p")
        yield Feature(**properties)
