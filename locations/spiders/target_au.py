import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class TargetAUSpider(scrapy.Spider):
    name = "target_au"
    item_attributes = { 'brand': "Target", 'brand_wikidata': "Q7685854" }
    allowed_domains = ["target.com.au"]
    states = ["nsw","vic","qld","nt", "act", "sa", "tas", "wa"]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0",
                "Referer": "https://www.target.com.au/store-finder"}

    custom_settings = {'DOWNLOAD_DELAY' : 0.5,}

    def start_requests(self):
        url = "https://www.target.com.au/store-finder/state/{}"
        for state in self.states:
            yield scrapy.Request(url.format(state),headers=self.headers, callback=self.parse)


    def parse(self, response):
        store_links = response.xpath('//a[@class="table-tap-canonical"]/@href').getall()
        for link in store_links:
            yield scrapy.Request(response.urljoin(link), callback=self.parse_store, headers=self.headers)

    def _parse_hour_str(self, hour_string):
        time_, am_pm = tuple(hour_string.split(" "))
        hour, min = tuple(time_.split(":"))
        hour = int(hour)
        if am_pm == "PM":
            hour += 12
        return f"{hour}:{min}"

    def parse_hours(self, hours_node):
        opening_hours = OpeningHours()
        days = hours_node.xpath(".//dt/text()").getall()
        hours = hours_node.xpath(".//dd/text()").getall()
        for idx, day in enumerate(days):
            store_hours = hours[idx]
            if "–" not in store_hours or ":" not in store_hours:
                continue
            parts = store_hours.strip().split(" – ")
            open_time = self._parse_hour_str(parts[0])
            close_time = self._parse_hour_str(parts[1])
            opening_hours.add_range(day[0:2], open_time, close_time)
        
        return opening_hours.as_opening_hours()



    def parse_store(self, response):
        store_name = response.xpath("//h4/text()").get().replace("Target – ","")
        address_header = response.xpath("//span[@itemprop='streetAddress']/strong/text()").get()
        address = " ".join(response.xpath("//span[@itemprop='streetAddress']/text()").getall()).strip()
        if address_header:
            address = address_header + " " + address
        locality = response.xpath("//span[@itemprop='addressLocality']/text()").get()
        region = response.xpath("//span[@itemprop='addressRegion']/text()").get()
        post_code = response.xpath("//span[@itemprop='postalCode']/text()").get()
        phone_number = response.xpath("//span[@itemprop='telephone']/text()").get()
        hours_section = response.xpath("(//dl)[1]")[0]
        opening_hours = self.parse_hours(hours_section)
        lat = response.xpath("//div[@data-embedded-json='store-content-data']//@data-lat").get()
        lon = response.xpath("//div[@data-embedded-json='store-content-data']//@data-lng").get()

        yield GeojsonPointItem(lat=lat,
                                lon=lon,
                                name=store_name,
                                addr_full=address,
                                city=locality,
                                state=region,
                                postcode=post_code,
                                country="AU",
                                phone=phone_number,
                                website=response.url,
                                opening_hours=opening_hours,
                                ref=response.url.split("/")[-1])  
