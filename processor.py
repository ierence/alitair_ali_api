from lxml import etree as et
from dataclasses import dataclass
import click


@dataclass
class MerchantProduct:
    product_id: str
    retail_price: str
    base_retail_price: str
    whole_price: str
    base_whole_price: str
    discount: str
    inventory_id: str
    inventory: str


def extract_merchant_data(filename):
    # Load relevant merchant data
    merchant_products = {}
    with open(f'feeds/{filename}', 'rb') as f:
        data = f.read()
        merchant_tree = et.XML(data, parser=et.XMLParser(strip_cdata=False))

    for product in merchant_tree.findall('product'):
        price = product.find('price')
        inventory = product.find('assortiment/assort')
        merchant_products[product.attrib['prodID']] = MerchantProduct(
            product_id=product.attrib['prodID'],
            retail_price=price.attrib['RetailPrice'],
            base_retail_price=price.attrib['BaseRetailPrice'],
            whole_price=price.attrib['WholePrice'],
            base_whole_price=price.attrib['BaseWholePrice'],
            discount=price.attrib['Discount'],
            inventory_id=inventory.attrib['aID'],
            inventory=inventory.attrib['sklad']
        )
    return merchant_products


def update_our_xml(filename, target_filename, merchant_products: dict):
    our_tree = et.parse(f'feeds/{filename}')

    for offer in our_tree.findall(f'.//offer'):
        offer_id = offer.attrib['id']
        if offer_id in merchant_products.keys():
            product = merchant_products[offer_id]

            # Update Price
            price = offer.find('price')
            price.attrib['RetailPrice'] = product.retail_price
            price.attrib['BaseRetailPrice'] = product.base_retail_price
            price.attrib['WholePrice'] = product.whole_price
            price.attrib['BaseWholePrice'] = product.base_whole_price
            # Update Inventory
            quantity = offer.find('quantity')
            quantity.text = product.inventory

    # Restore CDATA
    for desc in our_tree.findall('.//description'):
        desc.text = et.CDATA(desc.text)

    with open(f'feeds/{target_filename}', 'wb') as f:
        string = et.tostring(our_tree, encoding='utf-8', method='xml')
        f.write(string)


@click.command()
@click.option('--m', type=str, required=True,
              help='Имя файла с фидом поставщика в папке /feeds')
@click.option('--o', type=str, required=True,
              help='Имя файла с нашим фидом /feeds')
@click.option('--n', type=str, required=False, default=None,
              help='Опциональный аргумент. Сохраняет обновлённый фид в новый файл в /feeds')
def main(m, o, n):
    if n is None:
        n = o

    merchant_products = extract_merchant_data(m)
    update_our_xml(o, n, merchant_products)


if __name__ == '__main__':
    main()
