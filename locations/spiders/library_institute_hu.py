import scrapy
from scrapy import Request

from locations.categories import Categories, apply_category
from locations.items import Feature


class LibraryInstituteHUSpider(scrapy.Spider):
    name = "library_institute_hu"
    start_urls = [
        "https://www.ki.oszk.hu/informacioszolgaltatas/magyarorszagi-konyvtarak-adatbazisa?search=&megye=all&konyvtartipus=all&nyilvanos=on&submit=Start+a+search"
    ]
    custom_settings = {"DOWNLOAD_TIMEOUT": 1800}  # start_urls Page takes a while to load

    def parse(self, response):
        locations = response.xpath('//div[@id="mka_talalatilista"]/a')
        for location in locations:
            url = location.xpath(".//@href").get()
            name = location.xpath('.//div[@class="mka_nev"]/text()').get()
            addr_full = location.xpath('.//div[@class="mka_cim"]/text()').get()
            yield Request(
                url,
                callback=self.parse_library,
                cb_kwargs={"name": name, "addr_full": addr_full},
            )

    def parse_library(self, response, name, addr_full):
        props = {"ref": response.url, "name": name, "addr_full": addr_full, "country": "HU", "extras": {}}

        blank_a_targets = response.xpath('//a[@target="_blank"]/@href').getall()
        for url in blank_a_targets:
            if "google.com/maps" in url:
                props["lat"], props["lon"] = self.unpack_g_maps_coord(url)
                break

        labels = response.xpath('//span[@class="nykj_label"]/text()').getall()
        values = response.xpath('//span[@class="nykj_content"]')

        # Get Phone and Fax
        phone = self.get_node("Telefonszám:", labels, values)
        if phone:
            for phone in phone.xpath(".//li/text()").getall():
                if "(fax)" in phone.lower():
                    props["extras"]["fax"] = phone[: phone.find("(fax)")].strip()
                else:
                    props["phone"] = phone[: phone.find("(")].strip()

        # Get Website
        website = self.get_node("Honlapcím:", labels, values)
        if website:
            props["website"] = website.xpath(".//a/@href").get()

        apply_category(Categories.LIBRARY, props)

        yield Feature(**props)

    @staticmethod
    def get_node(label_to_find, labels, values):
        """
        Function that returns the equivalent node given the label to find in labels
        label_to_find: str - The label to find- e.g. "Telefonszám"
        labels: list - The list of labels
        values: list - The list of values
        """
        for label, value in zip(labels, values):
            if label == label_to_find:
                return value

    def unpack_g_maps_coord(self, url: str):
        """
        Function that unpacks the coordinates from a google maps URL
        url: str - google maps url
        """
        try:
            return url.rsplit("/", 1)[1].split("+")[0], url.rsplit("/", 1)[1].split("+")[1]
        except:
            self.crawler.stats.inc_value("atp/library_institute_hu/unpack_g_maps_coord_error")
