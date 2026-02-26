from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QDialogButtonBox,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QCheckBox,
    QLabel,
)
from PyQt5.QtCore import Qt


class ParameterDialog(QDialog):
    def __init__(self, param_spec: dict, title="Analysis Parameters", parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(400, 300)

        self.param_spec = param_spec
        self.widgets = {}

        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self._build_form()

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addWidget(self.button_box)

    # ---------------------------------------------------------

    def _build_form(self):

        for key, spec in self.param_spec.items():

            label = spec.get("label", key)
            field_type = spec.get("type", "float")

            if field_type == "int":
                widget = QSpinBox()
                widget.setMinimum(spec.get("min", -10_000_000))
                widget.setMaximum(spec.get("max", 10_000_000))
                widget.setValue(spec.get("default", 0))

            elif field_type == "float":
                widget = QDoubleSpinBox()
                widget.setDecimals(6)
                widget.setMinimum(spec.get("min", -1e9))
                widget.setMaximum(spec.get("max", 1e9))
                widget.setSingleStep(spec.get("step", 0.1))
                widget.setValue(spec.get("default", 0.0))

            elif field_type == "choice":
                widget = QComboBox()
                options = spec.get("options", [])
                widget.addItems(options)

                if "default" in spec and spec["default"] in options:
                    widget.setCurrentText(spec["default"])

            elif field_type == "bool":
                widget = QCheckBox()
                widget.setChecked(spec.get("default", False))

            else:
                widget = QLabel("Unsupported type")

            self.widgets[key] = widget
            self.form_layout.addRow(label, widget)

    # ---------------------------------------------------------

    def get_values(self):

        values = {}

        for key, widget in self.widgets.items():

            if isinstance(widget, QSpinBox):
                values[key] = widget.value()

            elif isinstance(widget, QDoubleSpinBox):
                values[key] = widget.value()

            elif isinstance(widget, QComboBox):
                values[key] = widget.currentText()

            elif isinstance(widget, QCheckBox):
                values[key] = widget.isChecked()

        return values