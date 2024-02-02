from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class SpotlightSpider(SitemapSpider):
    name = "spotlight"
    item_attributes = {"brand": "Spotlight", "brand_wikidata": "Q105960982"}
    allowed_domains = ["www.spotlightstores.com"]
    sitemap_urls = [
        "https://www.spotlightstores.com/sitemap/store/store-sitemap.xml",
        "https://www.spotlightstores.com/nz/sitemap/store/store-sitemap.xml",
        "https://www.spotlightstores.com/sg/sitemap/store/store-sitemap.xml",
        "https://www.spotlightstores.com/my/sitemap/store/store-sitemap.xml",
    ]
    sitemap_rules = [(r"\/store\/(?:[^\/]+\/){2}s\d+$", "parse")]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "REDIRECT_ENABLED": False,
    }

    def parse(self, response):
        properties = {
            "ref": response.xpath('//div[@id="maps_canvas"]/@data-storeid').get(),
            "name": response.xpath('//div[@id="maps_canvas"]/@data-storename').get(),
            "lat": response.xpath('//div[@id="maps_canvas"]/@data-latitude').get(),
            "lon": response.xpath('//div[@id="maps_canvas"]/@data-longitude').get(),
            "addr_full": " ".join(
                (
                    " ".join(response.xpath('//div[contains(@class, "store-detail-desc")]/ul[1]/li/text()').getall())
                ).split()
            ),
            "phone": response.xpath('//a[contains(@class, "call-store")]/@href').get().replace("tel:", ""),
            "website": response.url,
        }

        oh = OpeningHours()
        hours_raw = (
            " ".join((" ".join(response.xpath("(//table)[2]/tbody/tr/td/text()").getall())).split())
            .replace(" to ", " ")
            .replace("Closed", "12:00am 12:00am")
            .split()
        )
        hours_raw = [hours_raw[n : n + 3] for n in range(0, len(hours_raw), 3)]
        for day in hours_raw:
            if day[1].upper() == "12:00am" and day[2].upper() == "12:00am":
                continue
            oh.add_range(DAYS_EN[day[0]], day[1].upper(), day[2].upper(), "%I:%M%p")
        properties["opening_hours"] = oh.as_opening_hours()

        yield Feature(**properties)
