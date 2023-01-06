import scrapy

from locations.items import GeojsonPointItem


class RaSushiSpider(scrapy.spiders.SitemapSpider):
    name = "ra_sushi"
    item_attributes = {
        "brand": "RA Sushi",
    }

    sitemap_urls = ["https://rasushi.com/stores-sitemap.xml"]
    sitemap_rules = [("/locations/", "parse_store")]

    def parse_store(self, response):
        location = response.xpath("//div[@id='store_locator_single_map']")
        address = response.xpath("//span[@class='addressGet']//text()").extract()
        type = response.xpath("//span[@class='devOp1']/text()").extract_first()
        addr_dict = self.parse_address(address, type)

        yield GeojsonPointItem(
            ref=response.url.split("/")[-2],
            name=response.xpath("//h1[@class='title']/text()").extract_first().strip(),
            lat=location.xpath("@data-lat").extract_first(),
            lon=location.xpath("@data-lng").extract_first(),
            street_address=addr_dict.get("street_addresss", None),
            city=addr_dict["city"],
            state=addr_dict["state"],
            postcode=addr_dict.get("postcode", None),
            country="US",
            phone=response.xpath("//a[@class='telLoc']/text()").extract_first(),
            website=response.url,
        )

    @staticmethod
    def parse_address(address, type):
        if "Delivery Only" in type:
            if len(address) == 1:
                addr_dict = {
                    "city": address[0].split(",")[0].strip(),
                    "state": address[0].split(",")[1].strip().split(" ")[0].strip(),
                }
            else:
                addr_dict = {
                    "city": address[0].strip(),
                    "state": address[1].strip().split(" ")[0].strip(),
                }
        else:
            city_state = address[-1]
            addr_dict = {
                "street_address": ",".join(address[0:2]) if len(address) == 3 else address[0].strip(),
                "city": city_state.split(",")[0].strip(),
                "state": city_state.split(",")[1].strip().split(" ")[0].strip(),
                "postcode": city_state.split(",")[-1].strip().split(" ")[1].strip(),
            }

        return addr_dict
