import scrapy

from locations.items import Feature


class CleanHarborsSpider(scrapy.Spider):
    name = "clean_harbors"
    item_attributes = {"operator": "Clean Harbors", "operator_wikidata": "Q5130494"}
    allowed_domains = ["cleanharbors.com"]
    start_urls = ("https://www.cleanharbors.com/locations/united-states",)

    def parse(self, response):
        urls = response.xpath('//span[@class="field-content"]//a/@href').extract()
        for url in urls:
            if url.startswith("tel"):
                pass
            else:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):
        lati = response.xpath('//meta[@property="latitude"]').extract_first()
        longi = response.xpath('//meta[@property="longitude"]').extract_first()
        lat = lati.split("content=")[1].strip('">')
        lon = longi.split("content=")[1].strip('">')
        phone = (
            response.xpath('//*[@id="block-clean-harbor-content"]/div/article/div/div[1]/div[2]/div[1]/div[2]/div[2]')
            .extract_first()
            .split(">")[2]
            .strip("</a<div")
        )
        if phone.startswith("span"):
            phone = "NULL"
        try:
            add = response.xpath('//span[@class="address-line1"]//text()').extract_first()
            city = response.xpath('//span[@class="locality"]//text()').extract_first()
            state = response.xpath('//span[@class="administrative-area"]//text()').extract_first()
            ref = add + city + state
        except:
            add = (
                response.xpath('//span[@class="address-line1"]//text()').extract_first()
                + " "
                + response.xpath('//span[@class="address-line2"]//text()').extract_first()
            )
            city = response.xpath('//span[@class="locality"]//text()').extract_first()
            state = None
            ref = add + city
        properties = {
            "ref": ref,
            "name": response.xpath('//span[@class="organization"]//text()').extract_first(),
            "street_address": add,
            "city": city,
            "state": state,
            "postcode": response.xpath('//span[@class="postal-code"]//text()').extract_first(),
            "country": response.xpath('//span[@class="country"]//text()').extract_first(),
            "phone": phone,
            "lat": float(lat),
            "lon": float(lon),
        }

        yield Feature(**properties)
