import sys
import inspect
import importlib
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDialog,
    QListWidget, QListWidgetItem
)
from src.python import RigidBody  # your physics base class
from src.python import main


def get_subclasses(module_path, base_class):
    """Return all subclasses of base_class inside given module."""
    module = importlib.import_module(module_path)
    subclasses = []
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, base_class) and obj is not base_class:
            subclasses.append(obj)
    return subclasses

import pkgutil
import src  # root package of your project


def get_all_subclasses(base_class, root_pkg=src):
    """Find subclasses of base_class across the entire src package."""
    subclasses = []
    package_path = os.path.dirname(root_pkg.__file__)

    for finder, name, ispkg in pkgutil.walk_packages([package_path], root_pkg.__name__ + "."):
        try:
            module = importlib.import_module(name)
        except Exception as e:
            # Some modules might require game context -> skip
            continue

        for _, obj in inspect.getmembers(module, inspect.isclass):
            try:
                if issubclass(obj, base_class) and obj is not base_class:
                    subclasses.append(obj)
            except Exception:
                pass
    return subclasses

def is_src_object(obj):
    """Check if object's class is from /src directory."""
    try:
        module_file = inspect.getfile(obj.__class__)
        return os.path.abspath("../src") in os.path.abspath(module_file)
    except Exception:
        return False


class ObjectTreeApp(QMainWindow):
    def __init__(self, root_object):
        super().__init__()
        self.setWindowTitle("Object Tree Viewer")
        self.resize(1000, 600)

        # Layouts
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # Tree (left side)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Object Tree")
        layout.addWidget(self.tree, 2)

        # Properties (right side with 2 columns)
        self.properties = QTreeWidget()
        self.properties.setColumnCount(2)
        self.properties.setHeaderLabels(["Property", "Value"])
        layout.addWidget(self.properties, 2)

        # Bottom + button
        self.add_button = QPushButton("+")
        layout.addWidget(self.add_button, 0)

        # Populate tree
        self.populate_tree(root_object, self.tree.invisibleRootItem())

        # Connect signals
        self.tree.currentItemChanged.connect(self.display_properties)
        self.add_button.clicked.connect(self.show_class_selector)

    def populate_tree(self, obj, parent_item):
        item = QTreeWidgetItem([obj.__class__.__name__])
        item.obj_ref = obj
        parent_item.addChild(item)

        # scan attributes
        if hasattr(obj, "__dict__"):
            for attr, value in vars(obj).items():
                if is_src_object(value):
                    self.populate_tree(value, item)
                elif isinstance(value, (list, tuple, set)):
                    for v in value:
                        if is_src_object(v):
                            self.populate_tree(v, item)
                elif isinstance(value, dict):
                    for v in value.values():
                        if is_src_object(v):
                            self.populate_tree(v, item)

    # def populate_tree(self, obj, parent_item):
    #     """Recursively populate tree with /src objects; other attributes go to properties."""
    #     item = QTreeWidgetItem([obj.__class__.__name__])
    #     item.obj_ref = obj
    #     parent_item.addChild(item)
    #
    #     # Only expand objects from /src
    #     if hasattr(obj, "__dict__"):
    #         for attr, value in vars(obj).items():
    #             if is_src_object(value):
    #                 self.populate_tree(value, item)
    #             elif isinstance(value, list):  # handle lists
    #                 for v in value:
    #                     if is_src_object(v):
    #                         self.populate_tree(v, item)
    #             # Non-src objects go into properties, not tree
        return item

    def display_properties(self, current, prev):
        """Display non-src fields of selected object in property list."""
        if not current:
            return
        obj = current.obj_ref
        self.properties.clear()

        if not hasattr(obj, "__dict__"):
            return

        for attr, value in vars(obj).items():
            if is_src_object(value):
                continue  # handled in tree
            if isinstance(value, list) and all(is_src_object(v) for v in value):
                continue  # handled in tree

            # Otherwise, show in property list
            QTreeWidgetItem(self.properties, [attr, str(value)])

    def show_class_selector(self):
        """Open dialog with all subclasses of RigidBody."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select RigidBody subclass")
        layout = QVBoxLayout(dialog)

        rigidbody_classes = get_all_subclasses(RigidBody)
        subclasses = rigidbody_classes
        # subclasses = get_subclasses("src.shared.physics.objects", RigidBody)
        list_widget = QListWidget()
        for cls in subclasses:
            item = QListWidgetItem(cls.__name__)
            item.cls_ref = cls
            list_widget.addItem(item)
        layout.addWidget(list_widget)

        ok_button = QPushButton("Create")
        layout.addWidget(ok_button)

        def create_selected():
            selected = list_widget.currentItem()
            if selected:
                cls = selected.cls_ref
                new_obj = cls()  # instantiate (: handle ctor args if needed)
                print("Created:", new_obj)
            dialog.accept()

        ok_button.clicked.connect(create_selected)
        dialog.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ObjectTreeApp(main.client)  # pass your client from main.py
    viewer.show()
    sys.exit(app.exec_())
