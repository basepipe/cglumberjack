import nuke
def run():
    if nuke.selectedNode().Class() == 'Read':
            
        selectedFormat = nuke.selectedNode()['format'].value()
        
        nuke.root()['format'].setValue(selectedFormat)
        nuke.message('Comp size has been set!!!!')
