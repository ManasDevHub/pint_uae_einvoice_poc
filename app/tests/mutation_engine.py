from lxml import etree
import os

class XMLMutationEngine:
    def __init__(self, template_path: str):
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found at {template_path}")
        self.template_path = template_path
        self.ns = {
            'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
        }

    def mutate(self, mutations: list) -> str:
        """
        Accepts a list of mutations. Each mutation is a dict:
        { 'xpath': '...', 'value': '...', 'action': 'update' | 'remove' | 'add' }
        Returns the mutated XML string.
        """
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(self.template_path, parser)
        root = tree.getroot()

        for mut in mutations:
            xpath = mut.get('xpath')
            value = mut.get('value')
            action = mut.get('action', 'update')

            nodes = root.xpath(xpath, namespaces=self.ns)
            
            if action == 'update':
                for node in nodes:
                    node.text = str(value)
            elif action == 'remove':
                for node in nodes:
                    parent = node.getparent()
                    if parent is not None:
                        parent.remove(node)
            elif action == 'add':
                # Basic implementation for adding: assumes parent xpath is provided
                parent_xpath = mut.get('parent_xpath')
                tag_name = mut.get('tag') # e.g. 'cbc:Note'
                parents = root.xpath(parent_xpath, namespaces=self.ns)
                for p in parents:
                    # Parse the tag (handle prefix)
                    prefix, localname = tag_name.split(':')
                    new_node = etree.SubElement(p, etree.QName(self.ns[prefix], localname))
                    new_node.text = str(value)

        return etree.tostring(tree, encoding='UTF-8', xml_declaration=True, pretty_print=True).decode('utf-8')

# Example Usage:
# engine = XMLMutationEngine('data/sample_invoice.xml')
# xml = engine.mutate([{'xpath': '//cbc:ID', 'value': 'TEST-001'}])
