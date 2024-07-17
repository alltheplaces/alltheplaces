import scrapy

from locations.items import Feature

regex_street = (
    r"^(\s?\d{1,5}\s[a-zA-Z]+\.?\s?\#?\d{0,5}[a-zA-Z]{0,10}"
    r"\.?\s?\#?\d{0,5}[a-zA-Z]{0,10}\.?\s?\#?\d{0,5}[a-zA-Z]{0,10})"
)
regex_cty_st_zip = r"^(\s?[a-zA-z]+\s?[a-zA-z]{0,10},\sWA\.?\s\d{5})"
regex_phone = r"^\s?\d{3}\.\d{3}\.\d{4}"
regex_name = r"^(\s?[a-zA-z]+/?\s?[a-zA-z]{0,10}\s?Bob's)"


class BobsBurgersSpider(scrapy.Spider):
    name = "bobs_burgers"
    item_attributes = {"brand": "Bob's Burgers"}
    allowed_domains = ["www.bobsburgersandbrew.com"]
    start_urls = ["https://www.bobsburgersandbrew.com/content/locations/locations"]

    def parse(self, response):
        names = response.xpath(
            '//td[contains(@style,"300px") and contains(' '., "MAP")]/descendant-or-self::*/text()'
        ).re(regex_name)

        streets = response.xpath(
            '//td[contains(@style,"300px") and contains(' '., "MAP")]/descendant-or-self::*/text()'
        ).re(regex_street)

        phones = response.xpath(
            '//td[contains(@style,"300px") and contains(' '., "MAP")]/descendant-or-self::*/text()'
        ).re(regex_phone)

        cities = response.xpath(
            '//td[contains(@style,"300px") and contains(' '., "MAP")]/descendant-or-self::*/text()'
        ).re(regex_cty_st_zip)

        stores = response.xpath('//td[contains(@style,"300px") and contains(., "MAP")]')
        for i in range(len(stores)):
            name = names[i].strip("\xa0").strip()
            street = streets[i].strip()
            city = cities[i].split(",")[0].strip()
            cities[i] = cities[i].replace("WA.", "WA ").strip()
            postcode = cities[i].split("WA ")[1].strip()
            addr_full = "{} {}, WA {}".format(street, city, postcode).strip()
            phone = phones[i].replace(".", " ").strip()

            yield Feature(
                ref=name,
                name=name,
                street=street,
                city=city,
                state="WA",
                postcode=postcode,
                addr_full=addr_full,
                phone=phone,
            )
