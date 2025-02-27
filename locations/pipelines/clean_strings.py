import html

from scrapy import Spider

from locations.items import Feature


def clean_string(val: str) -> str:
    return html.unescape(val).strip()


class CleanStringsPipeline:
    skipped_keys = {"ref", "website"}

    def process_item(self, item: Feature, spider: Spider):
        for key, value in item.items():
            if key in self.skipped_keys:
                continue
            if not isinstance(value, str):
                continue

            cleaned_value = clean_string(value)
            if cleaned_value != value:
                item[key] = cleaned_value
                spider.crawler.stats.inc_value("atp/clean_strings/{}".format(key))

        return item
