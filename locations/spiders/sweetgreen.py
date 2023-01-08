import scrapy

from locations.items import Feature


class SweetgreenSpider(scrapy.Spider):
    name = "sweetgreen"
    item_attributes = {"brand": "Sweetgreen", "brand_wikidata": "Q18636413"}
    allowed_domains = ["www.sweetgreen.com"]
    start_urls = ("http://www.sweetgreen.com/locations/",)

    def parse(self, response):
        location_hrefs = response.xpath('//a[contains(@class, "location")]')
        for location_href in location_hrefs:
            yield Feature(
                name=location_href.xpath("@title").extract_first(),
                addr_full=location_href.xpath("@data-street").extract_first(),
                phone=location_href.xpath("@data-phone").extract_first(),
                ref=location_href.xpath("@id").extract_first(),
                lon=float(location_href.xpath("@data-longitude").extract_first()),
                lat=float(location_href.xpath("@data-latitude").extract_first()),
            )
