import sys
from PyQt5.QtWidgets import QApplication
from controller import AppController
from window import Window

app = QApplication(sys.argv)

controller = AppController()
window = Window(controller)
window.show()

sys.exit(app.exec_())