import scrapy
from locations.items import GeojsonPointItem


class AverittSpider(scrapy.Spider):
    name = "averitt"
    item_attributes = {"brand": "Averitt Express", "brand_wikidata": "Q4828320"}
    allowed_domains = ["averitt.com"]
    start_urls = [
        "https://www.averitt.com/locations",
    ]

    def parse(self, response):
        states = response.xpath('//select[@name="state"]/option/@value').extract()
        for state in states:
            if state == "State":
                continue
            yield scrapy.FormRequest(
                url=response.urljoin(state.replace("..", "")),
                callback=self.parse_state,
            )

    def parse_state(self, response):
        centers = response.xpath(
            '//*[@id="hs_cos_wrapper_widget_1613430615107_"]/b/a/@href'
        ).extract()
        for center in centers:
            yield scrapy.Request(response.urljoin(center), callback=self.parse_center)

    def parse_center(self, response):
        # 1
        address_full = response.xpath(
            "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p[1]/span[1]/text()"
        ).get()
        city = response.xpath(
            "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p[1]/span[3]/text()"
        ).get()
        state = response.xpath(
            "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p[1]/span[5]/text()"
        ).get()
        postcode = response.xpath(
            "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p[1]/span[7]/text()"
        ).get()

        # 2
        if city == None:
            address_full = response.xpath(
                "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p[1]/span[2]/text()"
            ).get()
            city_state_postcode = response.xpath(
                "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p[1]/span[2]/text()"
            ).get()
            if address_full != None:
                postcode = city_state_postcode.split()[-1]
                state = city_state_postcode.split()[-2]
                city = " ".join(city_state_postcode.split()[:-2]).replace(",", "")

        # 3
        if city == None:
            address_full = response.xpath(
                "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p/text()"
            ).get()
            address = response.xpath(
                "string(/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p)"
            ).get()
            if address_full:
                city_state_postcode = address.replace(address_full, "")
                postcode = city_state_postcode.split()[-1]
                state = city_state_postcode.split()[-2]
                city = " ".join(city_state_postcode.split()[:-2]).replace(",", "")

        # 4
        if city == None:
            address_full = response.xpath(
                "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p[1]/span/text()"
            ).get()
            address = response.xpath(
                "string(/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/p[1]/span)"
            ).get()
            if address_full:
                city_state_postcode = address.replace(address_full, "")
                postcode = city_state_postcode.split()[-1]
                state = city_state_postcode.split()[-2]
                city = " ".join(city_state_postcode.split()[:-2]).replace(",", "")

        ref_map_url = (
            response.xpath(
                '//a[contains(@href,"goo.gl") or contains(@href, "g.page")]/@href'
            )
            .get()
            .replace("https://goo.gl/maps/", "")
            .replace("https://g.page/", "")
        )
        phone = response.xpath(
            "/html/body/div[2]/div/div[1]/div/div/span/div[2]/div/div/div/div[1]/div/div/p/a/text()"
        ).get()
        email = (
            response.xpath(
                "/html/body/div[2]/div/div[1]/div/div/span/div[2]/div/div/div/div[2]/div/div/span/a/@href"
            )
            .get()
            .replace("mailto:", "")
        )
        name = response.xpath(
            "/html/body/div[2]/div/div[1]/div/div/span/div[4]/div/div/div/div[2]/div/div/h3/strong/text()"
        ).get()
        properties = {
            "ref": "_" + ref_map_url,
            "name": name,
            "addr_full": address_full,
            "city": city,
            "state": state,
            "postcode": postcode,
            "phone": phone,
            "email": email,
        }

        yield GeojsonPointItem(**properties)
