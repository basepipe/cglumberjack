import click
import nuke
import os
import sys


def find_nodes(node_class, top_node=nuke.root()):
    if top_node.Class() == node_class:
        yield top_node
    elif isinstance(top_node, nuke.Group):
        for child in top_node.nodes():
            for found_node in find_nodes(node_class, child):
                yield found_node


def replace_in_path(input_script, find_pattern, replace_pattern, output_script=None, type_='Write'):
    """

    :param input_script:
    :param output_script:
    :param type_: This can be "Write" or "Read" for this current implementation as designed
    :param find_pattern:
    :param new_pattern:
    :return:
    """
    nuke.scriptOpen(input_script)
    nodes_ = [w for w in find_nodes(type_)]
    for n in nodes_:
        path = n['file'].value()
        print(n.name(), path)
        #path = path.replace(find_pattern, replace_pattern)
        #n['file'].setValue(path)
    # nuke.scriptSave(output_script)


if __name__ == '__main__':
    print('this is a test')


