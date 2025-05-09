import re

from scrapy import Request, Spider

from locations.items import Feature


class TheBarMethodCAUSSpider(Spider):
    name = "the_bar_method_ca_us"
    item_attributes = {"brand": "The Bar Method", "brand_wikidata": "Q117599728"}
    allowed_domains = ["barmethod.com"]
    start_urls = ["https://barmethod.com/locations/"]
    requires_proxy = "US"  # or CA

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//a[@class="studioname"]/@href').extract()
        for path in city_urls:
            if path == "https://barmethod.com/locations/bar-online/":
                continue
            yield Request(
                path.strip(),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        infos = response.xpath("string(/html/body/div/div/main/article/div[1]/div[2]/div/div/div[2])").get().split("\n")

        street_address = infos[0]

        match = re.match(r"^([^,]*), (\w{2}) *(\d{5})?$", infos[1])
        if match is not None:
            country = "US"
        else:
            match = re.match(r"^([^,]*), (\w{2}) *(\w{3} \w{3})?$", infos[1])
            country = "CA"
        city = match.group(1)
        state = match.group(2)
        postcode = match.group(3) if len(match.groups()) > 2 else None

        email = infos[2]
        phone = infos[3]

        name = response.xpath('//h1[@class="x-text-content-text-primary"]/text()').get()
        facebook = response.xpath('//a[contains(@href, "facebook")]/@href').get()
        ref = response.request.url.replace(self.start_urls[0], "_")

        properties = {
            "name": name,
            "ref": ref.strip("_/"),
            "street_address": street_address,
            "city": city,
            "state": state,
            "postcode": postcode,
            "country": country,
            "phone": phone,
            "email": email,
            "facebook": facebook,
            "website": response.url,
        }

        yield Feature(**properties)
