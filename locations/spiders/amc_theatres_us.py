from scrapy import Spider

from locations.items import Feature


class AMCTheatresUSSpider(Spider):
    name = "amc_theatres_us"
    item_attributes = {"brand": "AMC Theaters", "brand_wikidata": "Q294721"}
    allowed_domains = ["www.amctheatres.com"]
    start_urls = ["https://www.amctheatres.com/sitemaps/sitemap-theatres.xml"]
    requires_proxy = "US"

    def parse(self, response):
        response.selector.remove_namespaces()

        for theater_elem in response.xpath("//url"):
            properties = {
                "website": theater_elem.xpath(".//loc/text()").extract_first(),
                "name": theater_elem.xpath('.//Attribute[@name="title"]/text()').extract_first(),
                "ref": theater_elem.xpath('.//Attribute[@name="theatreId"]/text()').extract_first(),
                "street_address": theater_elem.xpath('.//Attribute[@name="addressLine1"]/text()').extract_first(),
                "city": theater_elem.xpath('.//Attribute[@name="city"]/text()').extract_first(),
                "state": theater_elem.xpath('.//Attribute[@name="state"]/text()').extract_first(),
                "postcode": theater_elem.xpath('.//Attribute[@name="postalCode"]/text()').extract_first(),
                "lat": theater_elem.xpath('.//Attribute[@name="latitude"]/text()').extract_first(),
                "lon": theater_elem.xpath('.//Attribute[@name="longitude"]/text()').extract_first(),
            }

            yield Feature(**properties)
