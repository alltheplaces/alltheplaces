import scrapy

from locations.items import Feature


class TherapieClinicSpider(scrapy.Spider):
    name = "therapie_clinic"
    item_attributes = {"brand": "Thérapie Clinic", "brand_wikidata": "Q123034602"}
    allowed_domains = ["www.therapieclinic.com"]
    start_urls = ["https://www.therapieclinic.com/our-clinics/"]

    def parse(self, response):
        stores = response.xpath('//div[@class="box-clinic"]')
        for store in stores:
            properties = {
                "ref": store.xpath('./div[@class="cl_rest_box"]/div[@class="clbox_website"]/a/@href').get(),
                "website": response.urljoin(
                    store.xpath('./div[@class="cl_rest_box"]/div[@class="clbox_website"]/a/@href').get()
                ),
                "name": store.xpath('./div[@class="box_small_box"]/div[@class="clbox_name"]/text()').get(),
                "street_address": store.xpath('./div[@class="cl_rest_box"]/div[@class="clbox_street"]/text()').get(),
                "city": store.xpath('./div[@class="cl_rest_box"]/div[@class="clbox_city"]/text()').get(),
                "postcode": store.xpath('./div[@class="cl_rest_box"]/div[@class="clbox_zip"]/text()').get(),
                "country": store.xpath('./div[@class="cl_rest_box"]/div[@class="clbox_country"]/text()').get(),
                "phone": store.xpath('./div[@class="cl_rest_box"]/div[@class="clbox_phone"]/text()')
                .get()
                .replace("Phone: ", ""),
            }
            link = store.xpath('./div[@class="cl_rest_box"]/div[@class="clbox_direction"]/a/@href').get()
            coords = link.split("=")[2]
            lat, lon = coords.split(",")
            properties["lat"] = lat.strip()
            properties["lon"] = lon.strip()

            yield Feature(**properties)
