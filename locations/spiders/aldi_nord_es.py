from scrapy.spiders import SitemapSpider

from locations.items import GeojsonPointItem


class AldiNordESSpider(SitemapSpider):
    name = "aldi_nord_es"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171373", "country": "ES"}
    allowed_domains = ["www.aldi.es"]
    sitemap_urls = ["https://www.aldi.es/.aldi-nord-sitemap-pages.xml"]
    sitemap_rules = [(r"\/encuentra-tu-supermercado\/.+\/.+\/.+\.html$", "parse_store")]

    def parse_store(self, response):
        properties = {
            "ref": response.xpath("//@data-store-id").get(),
            "name": response.xpath(
                '//div[@class="mod-overview-intro__content"]/h1/text()'
            ).extract_first(),
            "street_address": response.xpath(
                'normalize-space(//span[@itemprop="streetAddress"]//text())'
            ).extract_first(),
            "city": response.xpath(
                'normalize-space(//span[@itemprop="addressLocality"]//text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="postalCode"]//text())'
            ).extract_first(),
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)
