import html

from scrapy import Spider

from locations.items import Feature


def clean_string(val: str) -> str:
    return html.unescape(val).strip()


class CleanStringsPipeline:

    def process_item(self, item: Feature, spider: Spider):
        for key, value in item.items():
            if isinstance(value, str):
                cleaned_value = clean_string(value)
                if cleaned_value != value:
                    item[key] = cleaned_value
                    spider.crawler.stats.inc_value("atp/clean_strings/{}".format(key))
        return item
