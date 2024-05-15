# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
import scrapy


class Product(scrapy.Item):
    name_ar = scrapy.Field()
    name_en = scrapy.Field()
    description_ar = scrapy.Field()
    description_en = scrapy.Field()
    price_original = scrapy.Field()
    price_discounted = scrapy.Field()
    brand_ar = scrapy.Field()
    brand_en = scrapy.Field()
    link = scrapy.Field()
    sku = scrapy.Field()
    id = scrapy.Field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.setdefault(field_name, '')
            if isinstance(self[field_name], float):
                self[field_name] = round(self[field_name], 2)
