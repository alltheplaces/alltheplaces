import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class CleanHarborsSpider(scrapy.Spider):
    name = "clean_harbors"
    item_attributes = {"operator": "Clean Harbors", "operator_wikidata": "Q5130494"}
    allowed_domains = ["cleanharbors.com"]
    start_urls = ("https://www.cleanharbors.com/locations/united-states",)

    def parse(self, response):
        urls = response.xpath('//span[@class="field-content"]//a/@href').getall()
        for url in urls:
            if url.startswith("tel"):
                pass
            else:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):
        lati = response.xpath('//meta[@property="latitude"]').get()
        longi = response.xpath('//meta[@property="longitude"]').get()
        lat = lati.split("content=")[1].strip('">')
        lon = longi.split("content=")[1].strip('">')
        phone = (
            response.xpath('//*[@id="block-clean-harbor-content"]/div/article/div/div[1]/div[2]/div[1]/div[2]/div[2]')
            .get()
            .split(">")[2]
            .strip("</a<div")
        )
        if phone.startswith("span"):
            phone = "NULL"
        try:
            add = response.xpath('//span[@class="address-line1"]//text()').get()
            city = response.xpath('//span[@class="locality"]//text()').get()
            state = response.xpath('//span[@class="administrative-area"]//text()').get()
            ref = add + city + state
        except:
            add = (
                response.xpath('//span[@class="address-line1"]//text()').get()
                + " "
                + response.xpath('//span[@class="address-line2"]//text()').get()
            )
            city = response.xpath('//span[@class="locality"]//text()').get()
            state = None
            ref = add + city
        properties = {
            "ref": ref,
            "name": response.xpath('//span[@class="organization"]//text()').get(),
            "street_address": add,
            "city": city,
            "state": state,
            "postcode": response.xpath('//span[@class="postal-code"]//text()').get(),
            "country": response.xpath('//span[@class="country"]//text()').get(),
            "phone": phone,
            "lat": float(lat),
            "lon": float(lon),
        }

        item = Feature(**properties)
        apply_category(Categories.WASTEWATER_PLANT, item)
        yield item
