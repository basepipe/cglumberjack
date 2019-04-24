from Qt import QtCore, QtGui, QtWidgets
import sys, random

COLORS = {'done': QtGui.QColor(0, 0, 0),
          'in progress': QtGui.QColor(0, 1, 0),
          'not started': QtGui.QColor(1, 0, 0)
          }


class PieChart(QtWidgets.QGraphicsView):
    def __init__(self, in_progress, done, not_started):
        QtWidgets.QWidget.__init__(self)
        self.set_angle = 0
        self.count1 = 1
        colors = []
        self.total = in_progress + done + not_started

    def set_values(self, status):
        angle = round(float(status*5760)/self.total)
        ellipse = QtWidgets.QGraphicsEllipseItem(0, 0, 400, 400)
        ellipse.setPos(0, 0)
        ellipse.setStartAngle(self.set_angle)
        ellipse.setSpanAngle(angle)
        ellipse.setBrush(colours[self.count1])
        self.set_angle += angle
        self.count1 += 1
        scene.addItem(ellipse)


app = QtWidgets.QApplication(sys.argv)
scene = QtWidgets.QGraphicsScene()

families = [1,2,3,4,5,6,7,8,9,10]
total = 0
set_angle = 0
count1 = 0
colours = []
total = sum(families)

for count in range(len(families)):
    number = []
    for count in range(3):
        number.append(random.randrange(0, 255))
    colours.append(QtGui.QColor(number[0],number[1],number[2]))

for family in families:
    # Max span is 5760, so we have to calculate corresponding span angle
    angle = round(float(family*5760)/total)
    ellipse = QtWidgets.QGraphicsEllipseItem(0,0,400,400)
    ellipse.setPos(0,0)
    ellipse.setStartAngle(set_angle)
    ellipse.setSpanAngle(angle)
    ellipse.setBrush(colours[count1])
    set_angle += angle
    count1 += 1
    scene.addItem(ellipse)


view = QtWidgets.QGraphicsView(scene)
view.show()
app.exec_()