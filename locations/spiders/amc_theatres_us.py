from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS

AMC = {"brand": "AMC", "brand_wikidata": "Q294721"}


class AmcTheatresUSSpider(Spider):
    name = "amc_theatres_us"
    allowed_domains = ["www.amctheatres.com"]
    start_urls = ["https://www.amctheatres.com/sitemaps/sitemap-theatres.xml"]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response):
        response.selector.remove_namespaces()

        for theater_elem in response.xpath("//url"):
            properties = {
                "website": theater_elem.xpath(".//loc/text()").extract_first(),
                "ref": theater_elem.xpath('.//Attribute[@name="theatreId"]/text()').extract_first(),
                "street_address": theater_elem.xpath('.//Attribute[@name="addressLine1"]/text()').extract_first(),
                "city": theater_elem.xpath('.//Attribute[@name="city"]/text()').extract_first(),
                "state": theater_elem.xpath('.//Attribute[@name="state"]/text()').extract_first(),
                "postcode": theater_elem.xpath('.//Attribute[@name="postalCode"]/text()').extract_first(),
                "lat": theater_elem.xpath('.//Attribute[@name="latitude"]/text()').extract_first(),
                "lon": theater_elem.xpath('.//Attribute[@name="longitude"]/text()').extract_first(),
            }

            label = theater_elem.xpath('.//Attribute[@name="title"]/text()').get()
            screens = label.rsplit(" ", 1)[1]
            if screens.isnumeric():
                properties["extras"] = {"screen": screens}
                label = label.rsplit(" ", 1)[0]

            if label.startswith("AMC"):
                properties.update(AMC)
            if label.startswith("AMC CLASSIC "):
                properties["name"] = "AMC Classic"
                properties["branch"] = label.removeprefix("AMC CLASSIC ")
            elif label.startswith("AMC DINE-IN "):
                properties["name"] = "AMC Dine-In"
                properties["branch"] = label.removeprefix("AMC DINE-IN ")
            elif label.startswith("AMC "):
                properties["name"] = "AMC"
                properties["branch"] = label.removeprefix("AMC ")
            else:
                properties["name"] = label

            apply_category(Categories.CINEMA, properties)

            yield Feature(**properties)
