import re

from scrapy.spiders import SitemapSpider

from locations.items import Feature


class PlannedParenthoodSpider(SitemapSpider):
    name = "planned_parenthood"
    item_attributes = {
        "operator": "Planned Parenthood",
        "operator_wikidata": "Q2553262",
        "country": "US",
    }
    allowed_domains = ["www.plannedparenthood.org"]
    sitemap_urls = ["https://www.plannedparenthood.org/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.plannedparenthood\.org\/health-center\/[-\w]+\/[-\w]+\/(\d+)\/[-\w]+$",
            "parse_venue",
        )
    ]
    # Note source Microdata is malformed

    def parse_venue(self, response):
        if response is None:
            # Ignoring redirects
            return

        properties = {
            "street_address": response.xpath('//*[@itemprop="streetAddress"]/text()').extract_first(),
            "city": response.xpath('//*[@itemprop="addressLocality"]/text()').extract_first(),
            "state": response.xpath('//*[@itemprop="addressRegion"]/text()').extract_first(),
            "postcode": response.xpath('//*[@itemprop="postalCode"]/text()').extract_first(),
            "phone": response.xpath('//a[@itemprop="telephone"][@data-link]/text()').extract_first(),
            "ref": response.url,
            "website": response.url,
        }

        if map_image := response.xpath('//img[@class="address-map"]/@data-lazy-interchange').get():
            if match := re.search(r"center=(.*?),(.*?)&zoom", map_image):
                properties["lat"] = float(match.group(1))
                properties["lon"] = float(match.group(2))

        yield Feature(**properties)
