from genericpath import isdir
import os
import imghdr
from unicodedata import name
from send2trash import send2trash
from pickle import TRUE
import sys
import shutil
import numpy
from pathlib import Path
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QTreeView, QFileSystemModel, QHBoxLayout, QVBoxLayout, QTextEdit, QLabel, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from pyqtgraph.opengl import GLViewWidget, MeshData, GLMeshItem
import stl
import pywavefront
from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtGui import QKeySequence, QPixmap

class FileSystemView(QWidget):
    def __init__(self, path_str):
        super().__init__()

        appWidth = 800
        appHeight = 400

        self.setWindowTitle('File Manager')
        self.setGeometry(300,300,appWidth,appHeight)

        path = Path(path_str)

        self.wasFileCopied = False
        self.copiedFile = ""
        self.newName = ""

        self.model = QFileSystemModel()
        self.model.setRootPath("")

        self.tree = QTreeView()
        self.tree.setModel(self.model)

        self.tree.expand(self.model.index(path.as_posix()))
        self.tree.expandAll()

        self.tree.selectionModel().currentChanged.connect(self.preview)
        self.tree.doubleClicked.connect(self.doubleClicked)

        self.tree.setColumnWidth(0, 300)        

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.tree, 1)

        self.currentPreview = None

        self.setLayout(self.layout)
            
        

    def doubleClicked(self, signal):
        index = self.tree.currentIndex()

        if not self.model.isDir(index):
            os.startfile(self.model.filePath(index))
            print("File run.")

    def keyPressEvent(self, event):
        index = self.tree.currentIndex()

        if event == QKeySequence.StandardKey.InsertParagraphSeparator:
            if self.model.isDir(index):
                self.tree.expand(index)
            else:
                os.startfile(self.model.filePath(index))
                print("File run.")

        if event == QKeySequence.StandardKey.Delete:
            file_path = self.model.filePath(index)
            file_path = file_path.replace("/","\\")
            send2trash(file_path)

            print("File/Folder sent to Recycle Bin")

        if event == QKeySequence.StandardKey.Copy:
            self.wasFileCopied = True
            self.copiedFile = self.model.filePath(index)
            print("Copied File")

        if event == QKeySequence.StandardKey.Cut:
            self.wasFileCopied = False
            self.copiedFile = self.model.filePath(index)
            print("Cut file")

        if event == QKeySequence.StandardKey.Paste and self.model.isDir(index):
            if os.path.exists(self.copiedFile):
                if self.wasFileCopied:
                    shutil.copy(self.copiedFile, self.model.filePath(index))
                    print("Pasted File. (Copied)")
                else:
                    print(self.copiedFile)
                    shutil.copy(self.copiedFile, self.model.filePath(index))
                    os.remove(self.copiedFile)
                    print("Pasted File. (Cut)")
            else:
                print("Missing file.")

            self.copiedFile = ""
            self.wasFileCopied = False

        if event == QKeySequence.StandardKey.New and not os.path.exists(self.model.filePath(index) + "/New folder"):
            os.mkdir(self.model.filePath(index) + "/New folder")
            print("New folder made.")
        elif event == QKeySequence.StandardKey.New and os.path.exists(self.model.filePath(index) + "/New folder"):
            print("Folder already exists here.")
        #Make it so that if a file is selected while creating a new folder, it creates the folder in the directory of the file.
        
        if event == QKeySequence.StandardKey.Replace:
            name = self.rename()
            newpath = Path(self.model.filePath(index)).resolve().parent.joinpath(name).as_posix()
            print(newpath)
            os.rename(self.model.filePath(index), newpath)
            
    def rename(self):
        name, done1 = QtWidgets.QInputDialog.getText(
             self, 'Rename', 'Enter New Name:')
        if done1:
             return name

    def preview(self, index):
        path = self.model.filePath(index)

        if self.currentPreview != None:
            self.layout.removeWidget(self.currentPreview)
            self.currentPreview = None

        try:
            with open(path, "rb") as f:
                content = f.read()
                self.currentPreview = PreviewPanel(path, content)
                self.layout.addWidget(self.currentPreview, 1)
        except Exception as e:
            print("Exception while trying to preview: " + str(e))




class PreviewPanel(QWidget):
    def __init__(self, path, content):
        super().__init__()

        layout = QVBoxLayout()

        label = QLabel()
        label.setText(os.path.basename(path))
        layout.addWidget(label, 0)

        imgtype = imghdr.what(None, h=content)

        if imgtype != None:
            view = QGraphicsView()
            pixmap = QPixmap(path)

            item = QGraphicsPixmapItem(pixmap)

            scene = QGraphicsScene()
            scene.addItem(item)

            view.setScene(scene)
            view.fitInView(item, Qt.KeepAspectRatio)
            layout.addWidget(view, 1)

        elif os.path.splitext(path)[1] == '.stl':
            stl_mesh = stl.mesh.Mesh.from_file(path)

            points = stl_mesh.points.reshape(-1, 3)
            faces = numpy.arange(points.shape[0]).reshape(-1, 3)

            layout.addWidget(self.create_glview(points, faces), 1)
        elif os.path.splitext(path)[1] == '.obj':
            scene = pywavefront.Wavefront(path)

            
            pass

        else:
            text = QTextEdit()
            text.setReadOnly(True)
            text.setText(content.decode("utf8"))
            layout.addWidget(text, 1)

        self.setLayout(layout)
    
    @staticmethod
    def create_glview(vertexes, faces):
        view = GLViewWidget()
        mesh_data = MeshData(vertexes=vertexes, faces=faces)
        mesh = GLMeshItem(meshdata=mesh_data, smooth=True, drawFaces=True, drawEdges=True, edgeColor=(0.8, 0.8, 0.8, 1))
        view.addItem(mesh)
        return view




if __name__ == '__main__':
    app = QApplication(sys.argv)


    demo = FileSystemView(".")
    demo.show()

    sys.exit(app.exec_())