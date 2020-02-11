import plugins.nuke.bin.preflight as preflight
import nuke
from cgl.ui.widgets.dialog import InputDialog
import os

def run():

    readNode = nuke.selectedNode()

    reformat = nuke.createNode('Reformat')
    proxyWrite = nuke.createNode('Write')
    reformat['type'].setValue('scale')
    reformat['scale'].setValue(0.5)
    proxyWrite['name'].setValue('proxyWrite')

    path = readNode['file'].evaluate()
    proxyFile = path.replace('high', 'proxy')

    reformatedName = proxyFile.split('.')
    reformatedName[-1] = '%04d'

    proxyFile = '.'.join(reformatedName)

    readNode['proxy'].setValue(proxyFile)
    proxyWrite['file'].setValue(proxyFile)
    proxyWrite['create_directories'].setValue(1)

    #proxyWrite['afterRender'].setValue('')
    #proxyWrite['selected'].setValue(1)

    if not os.path.isdir(os.path.dirname(proxyFile)):
        os.makedirs(os.path.dirname(proxyFile))

   

