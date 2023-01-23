from scrapy.spiders import SitemapSpider

from locations.items import Feature


class AldiNordPLSpider(SitemapSpider):
    name = "aldi_nord_pl"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171373", "country": "PL"}
    allowed_domains = ["www.aldi.pl"]
    sitemap_urls = ["https://www.aldi.pl/.aldi-nord-sitemap-pages.xml"]
    sitemap_rules = [(r"\/wyszukiwarka-sklepu\/.+\/.+\/.+\.html$", "parse_store")]

    def parse_store(self, response):
        properties = {
            "ref": response.xpath("//@data-store-id").get() or response.url,
            "name": response.xpath('//div[@class="mod-overview-intro__content"]/h1/text()').extract_first(),
            "street_address": response.xpath(
                'normalize-space(//span[@itemprop="streetAddress"]//text())'
            ).extract_first(),
            "city": response.xpath('normalize-space(//span[@itemprop="addressLocality"]//text())').extract_first(),
            "postcode": response.xpath('normalize-space(//span[@itemprop="postalCode"]//text())').extract_first(),
            "website": response.url,
        }

        yield Feature(**properties)
