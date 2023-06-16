import urllib.parse

from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class HomeDepotSpider(SitemapSpider):
    name = "homedepot"
    item_attributes = {"brand": "The Home Depot", "brand_wikidata": "Q864407"}
    allowed_domains = ["www.homedepot.com"]
    download_delay = 0.2
    sitemap_urls = ("https://www.homedepot.com/sitemap/d/store.xml",)
    sitemap_rules = [
        (r"^https:\/\/www.homedepot.com\/l\/.*\/\d*$", "parse_store"),
    ]
    requires_proxy = "US"

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "LocalBusiness")
        item["ref"] = item["website"].split("/")[-1]
        mapurl = urllib.parse.urlsplit(response.css('img[alt="map preview"]').attrib["src"])
        lat_lon = next(p for p in mapurl.path.split("/") if "," in p)
        lat, lon = lat_lon.split(",")
        item["lat"] = lat
        item["lon"] = lon
        yield item
