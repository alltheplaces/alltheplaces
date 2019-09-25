import json
import re
import scrapy

from locations.items import GeojsonPointItem


class StateFarmSpider(scrapy.Spider):
    name = "statefarm"
    allowed_domains = ["statefarm.com"]
    download_delay = 0.2

    start_urls = [
        'https://www.statefarm.com/agent/us',
    ]

    def parse_location(self, response):

        name = response.xpath('//*[@id="AgentNameLabelId"]//span[@itemprop="name"]/text()').extract_first()
        if name:
            name += ' - State Farm Insurance Agent'

        lat = response.xpath('//*[@id="agentOfficePrimaryLocLat"]/@value').extract_first()
        lon = response.xpath('//*[@id="agentOfficePrimaryLocLong"]/@value').extract_first()

        properties = {
            'ref': "_".join(response.url.split('/')[-3:]),
            'name': name,
            'addr_full':  response.xpath('normalize-space(//div[@itemtype="http://schema.org/PostalAddress"]//span[@id="locStreetContent_mainLocContent"]/text())').extract_first(),
            'city':  response.xpath('//div[@itemtype="http://schema.org/PostalAddress"]/div[2]/span/span[1]/text()').extract_first().strip(', '),
            'state':  response.xpath('//div[@itemtype="http://schema.org/PostalAddress"]/div[2]/span/span[2]/text()').extract_first(),
            'postcode':  response.xpath('//div[@itemtype="http://schema.org/PostalAddress"]/div[2]/span/span[3]/text()').extract_first(),
            'phone': response.xpath('normalize-space(//span[@id="offNumber_mainLocContent"]/span/text())').extract_first(),
            'lat': float(lat) if lat else None,
            'lon': float(lon) if lon else None,
            'website': response.url,
        }

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        agents = response.xpath('//div[contains(@id, "agent-details")]')
        # agent_sites = response.xpath('//a[contains(text(), "Visit agent site")]/@href').extract()

        if agents:
            for agent in agents:
                agent_site = agent.xpath('.//a[contains(text(), "Visit agent site")]/@href').extract_first()
                if not agent_site:
                    raise Exception('no agent site found')
                yield scrapy.Request(response.urljoin(agent_site), callback=self.parse_location)

        else:
            urls = response.xpath('//li/div/a/@href').extract()

            for url in urls:
                yield scrapy.Request(response.urljoin(url))


