import scrapy

from locations.google_url import url_to_coords
from locations.linked_data_parser import LinkedDataParser


def extract_google_position(item, response):
    for link in response.xpath("//a/@href").extract():
        if "maps.google.com" in link:
            item["lat"], item["lon"] = url_to_coords(link)
            return


class KwikFitGBSpider(scrapy.spiders.SitemapSpider):
    name = "kwikfit_gb"
    item_attributes = {
        "brand": "Kwik Fit",
        "brand_wikidata": "Q958053",
        "country": "GB",
    }
    sitemap_urls = ["https://www.kwik-fit.com/sitemap.xml"]
    sitemap_rules = [("/locate-a-centre/", "parse_store")]
    download_delay = 0.2

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "LocalBusiness")
        if item:
            item["ref"] = response.url
            extract_google_position(item, response)
            return item
