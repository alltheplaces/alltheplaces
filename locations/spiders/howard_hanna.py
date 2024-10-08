import re

from scrapy.spiders import SitemapSpider

from locations.items import Feature


class HowardHannaSpider(SitemapSpider):
    name = "howard_hanna"
    item_attributes = {"brand": "Howard Hanna", "brand_wikidata": "Q119573413"}
    allowed_domains = ["howardhanna.com"]
    sitemap_urls = ["https://www.howardhanna.com/Seo/OfficeSitemap"]
    sitemap_rules = [(r"/Office/Detail/", "parse")]

    def parse(self, response):
        info = response.css(".prop-main .row .row")[0]
        addr_full = info.css("div.font-13.font-sm-16").xpath("normalize-space()").get()
        properties = {
            "ref": response.url.split("/")[-1],
            "name": response.css("h1::text").get().strip(),
            "website": response.url,
            "phone": info.xpath('.//*[@title="Phone"]/../..//a/text()').get(),
            "extras": {
                "fax": info.xpath('.//*[@title="Fax"]/../..//a/text()').get(),
            },
            "addr_full": addr_full,
        }
        yield response.follow(
            response.css("a[href*=ViewOnStreet]")[0],
            meta={"properties": properties},
            callback=self.parse2,
        )

    def parse2(self, response):
        properties = response.meta["properties"]
        lat, lon = re.search(r"LatLng\('(.*)', '(.*)'\)", response.text).groups()
        properties.update(
            {
                "lat": lat,
                "lon": lon,
            }
        )
        yield Feature(**properties)
