import scrapy

from locations.items import Feature


class CoxHealthSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "cox_health"
    item_attributes = {"brand": "CoxHealth", "brand_wikidata": "Q5179867"}
    allowed_domains = ["coxhealth.com"]
    start_urls = ("https://www.coxhealth.com/our-hospitals-and-clinics/our-locations/",)

    def parse(self, response):
        urls = response.xpath('//div[@class="card-action"]//a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_loc)

    def parse_loc(self, response):
        name = response.xpath('//h2[@class="section-title"]/text()').extract_first()
        address = response.xpath('//div[@class="default-x-spacing reg-background module-card-new"]//p/text()').extract()
        x = response.xpath('//div[@class="map"]').extract()
        xy = x[0].split('"')
        address = " ".join(address)
        address = address.replace("\r", "").replace("\n", "")
        address = " ".join(address.split())
        address = address.split(" ")
        x = len(address) - 3
        add = " ".join(address)
        address1 = address[:x]
        address1 = " ".join(address1)
        city = address[x].replace(",", "")
        state = address[x + 1]
        zip = address[x + 2]
        if city == address[x].replace(",", "") == "West":
            x = len(address) - 4
            address1 = address[:x]
            address1 = " ".join(address1)
            city = address[x].replace(",", "") + " " + address[x + 1].replace(",", "")
            state = address[x + 2]
            zip = address[x + 3]
        elif city == address[x].replace(",", "") == "Ave.":
            address1 = "3555 S National Ave"
            address1 = " ".join(address1)
            city = "Springfield"
            state = "MO"
            zip = "65807"
        else:
            pass
        phone = response.xpath('//a[@class="phone"]/text()').extract()
        properties = {
            "ref": add,
            "name": name,
            "addr_full": address1,
            "city": city,
            "state": state,
            "postcode": zip,
            "country": "US",
            "phone": phone[0],
            "lat": float(xy[5].strip(",")),
            "lon": float(xy[3].strip(",")),
        }

        yield Feature(**properties)
