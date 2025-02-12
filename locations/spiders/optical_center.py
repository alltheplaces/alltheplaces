import html
import json

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class OpticalCenterSpider(SitemapSpider, StructuredDataSpider):
    name = "optical_center"
    item_attributes = {"brand": "Optical Center", "brand_wikidata": "Q3354448"}
    sitemap_urls = ["https://optician.optical-center.co.uk/sitemap.xml"]
    sitemap_rules = [("https://optician.optical-center.co.uk/", "parse_sd")]
    sitemap_follow = ["locationsitemap"]
    download_delay = 1
    requires_proxy = True
    drop_attributes = {"image"}

    def iter_linked_data(self, response):
        yield json.loads(response.xpath("//script[@data-lf-location-json]/text()").get())

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url.split("/")[-1]
        item["street_address"] = html.unescape(item["street_address"])
        item["city"] = html.unescape(item["city"])
        item["name"] = html.unescape(item["name"])

        # x-default is a lie, it's always FR, the whole thing is a lie, it's about domains not languages
        for link in response.xpath('//link[@rel="alternate"][@hreflang][@href]'):
            if link.attrib["hreflang"] == "x-default":
                continue
            item["extras"]["website:{}".format(link.attrib["hreflang"])] = link.attrib["href"]

        # Try to get the local url
        if item["country"] == "CA":
            item["website"] = item["extras"]["website:en"] = item["extras"]["website:en-CA"]
            item["extras"]["website:fr"] = item["extras"]["website:fr-CA"]
        elif item["country"] == "BE":
            item["website"] = item["extras"]["website:nl"]
        elif item["country"] == "CH":
            item["website"] = item["extras"]["website:de"]
        else:
            item["website"] = item["extras"].get("website:{}".format(item["country"].lower()), response.url)

        del item["extras"]["website:en-CA"]
        del item["extras"]["website:fr-CA"]

        yield item
