from scrapy.spiders import SitemapSpider
from locations.items import GeojsonPointItem


class BMSpider(SitemapSpider):
    name = "b_and_m"
    item_attributes = {"brand": "B&M", "brand_wikidata": "Q4836931"}
    allowed_domains = ["www.bmstores.co.uk"]
    sitemap_urls = ["https://www.bmstores.co.uk/hpcstores/storessitemap"]

    def parse(self, response):
        root = response.xpath(
            '//*[@itemscope][@itemtype="http://schema.org/LocalBusiness"]'
        )
        properties = {
            "ref": root.xpath('.//*[@itemprop="branchCode"]/text()').get(),
            "website": response.request.url,
            "name": root.xpath('.//*[@itemprop="name"]/text()').get(),
            "phone": root.xpath('.//*[@itemprop="telephone"]/text()').get(),
            "lat": root.xpath(
                './/*[@itemscope][@itemprop="geo"][@itemtype="http://schema.org/GeoCoordinates"]/meta[@itemprop="latitude"]/@content'
            ).get(),
            "lon": root.xpath(
                './/*[@itemscope][@itemprop="geo"][@itemtype="http://schema.org/GeoCoordinates"]/meta[@itemprop="longitude"]/@content'
            ).get(),
            "street_address": ", ".join(
                map(
                    lambda x: x.strip(),
                    root.xpath(
                        './/*[@itemscope][@itemprop="address"][@itemtype="http://schema.org/PostalAddress"]/*[@itemprop="streetAddress"]/text()'
                    ).getall(),
                )
            ).replace("\n", ", "),
            "city": root.xpath(
                './/*[@itemscope][@itemprop="address"][@itemtype="http://schema.org/PostalAddress"]/*[@itemprop="addressLocality"]/text()'
            ).get(),
            "postcode": root.xpath(
                './/*[@itemscope][@itemprop="address"][@itemtype="http://schema.org/PostalAddress"]/*[@itemprop="postalCode"]/text()'
            ).get(),
            "country": "GB",
            "brand": root.xpath('.//*[@class="bm-line-compact"]/text()').get(),
        }

        properties["phone"] = "+44 " + properties["phone"][1:]
        properties["addr_full"] = ", ".join(
            filter(
                None,
                (
                    properties["street_address"],
                    properties["city"],
                    root.xpath(
                        './/*[@itemscope][@itemprop="address"][@itemtype="http://schema.org/PostalAddress"]/*[@itemprop="addressRegion"]/text()'
                    ).get(),
                    properties["postcode"],
                    "United Kingdom",
                ),
            )
        )

        yield GeojsonPointItem(**properties)
