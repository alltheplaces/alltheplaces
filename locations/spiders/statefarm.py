import re
import scrapy

from locations.items import GeojsonPointItem


class StateFarmSpider(scrapy.Spider):
    name = "statefarm"
    item_attributes = {"brand": "State Farm", "brand_wikidata": "Q2007336"}
    allowed_domains = ["statefarm.com"]
    download_delay = 0.1

    start_urls = [
        "https://www.statefarm.com/agent/us",
    ]

    def parse_location(self, response):

        name = response.xpath('//span[@itemprop="name"]/text()').extract_first()
        if name:
            name += " - State Farm Insurance Agent"

        properties = {
            "ref": "_".join(response.url.split("/")[-3:]),
            "name": name,
            "addr_full": response.xpath(
                'normalize-space(//div[@itemtype="http://schema.org/PostalAddress"]//*[@itemprop="streetAddress"]/text())'
            ).extract_first(),
            "city": response.xpath(
                '//div[@itemtype="http://schema.org/PostalAddress"]//*[@itemprop="addressLocality"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '//div[@itemtype="http://schema.org/PostalAddress"]//*[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//div[@itemtype="http://schema.org/PostalAddress"]//*[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "phone": response.xpath(
                '//*[@itemprop="telephone"]/a/text()'
            ).extract_first(),
            "lat": float(response.xpath("//@data-latitude").extract_first()),
            "lon": float(response.xpath("//@data-longitude").extract_first()),
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        agents = response.xpath('//div[contains(@id, "agent-details")]')
        # agent_sites = response.xpath('//a[contains(text(), "Visit agent site")]/@href').extract()

        if agents:
            for agent in agents:
                agent_site = agent.xpath(
                    './/a[contains(text(), "Agent Website")]/@href'
                ).extract_first()
                if not agent_site:
                    raise Exception("no agent site found")
                yield scrapy.Request(
                    response.urljoin(agent_site), callback=self.parse_location
                )

        else:
            urls = response.xpath("//li/div/a/@href").extract()

            for url in urls:
                yield scrapy.Request(response.urljoin(url))
