from lxml import etree
from PyQt5.QtWidgets import QDialog, QComboBox, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, \
    QGridLayout, QWidget, QFormLayout

from utilities import MainEditFile


def configure_backend(parent):
    class BackendDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            backend = parent.project.property_get('backend')
            if backend:
                self.backend = backend['backend']
            else:
                self.backend = 'local'
            self.setWindowTitle('Run parameters for backend ' + self.backend)
            self.change_backend_box = QComboBox()
            self.change_backend_box.addItems(parent.project.backend_names())
            backend_index = parent.project.backend_names().index(self.backend)
            self.change_backend_box.setCurrentIndex(backend_index)
            parameters = parent.project.backend_parameters(self.backend)
            parameters_doc = parent.project.backend_parameters(self.backend, doc=True)

            self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            self.button_box.accepted.connect(self.accept)
            self.button_box.rejected.connect(self.reject)
            self.layout = QVBoxLayout()
            self.layout.addWidget(QLabel(
                'Current backend ' + self.backend + ' submission command:\n' + parent.project.backend_get(self.backend,
                                                                                                          'run_command') + '\nHost: ' + parent.project.backend_get(
                    self.backend, 'host')))
            if parameters:
                grid_layout = QGridLayout()
                self.parameter_values = {}
                row = 0
                for k in parameters.keys():
                    if v := parent.project.backend_parameter_get(self.backend, k):
                        parameters[k] = v
                    self.parameter_values[k] = QLineEdit(self)
                    self.parameter_values[k].setText(parameters[k])
                    grid_layout.addWidget(QLabel(k), row, 0)
                    grid_layout.addWidget(self.parameter_values[k], row, 1)
                    grid_layout.addWidget(QLabel(parameters_doc[k]), row, 2)
                    row += 1
                self.layout.addLayout(grid_layout)
            self.switch_layout = QHBoxLayout()
            self.switch_layout.addWidget(QLabel('Change to backend:'))
            self.switch_layout.addWidget(self.change_backend_box)
            self.layout.addLayout(self.switch_layout)
            # self.layout.addWidget(self.rawedit)
            self.layout.addWidget(self.button_box)
            self.setLayout(self.layout)

        def changed_backend(self):
            return self.change_backend_box.currentText()

    result = None
    while (dlg := BackendDialog(parent)) and (result := dlg.exec()) and dlg.changed_backend() != \
            parent.project.property_get('backend')['backend']:
        parent.project.property_set({'backend': dlg.changed_backend()})

    if result:
        parameters = parent.project.backend_parameters(dlg.backend)
        for parameter in parameters.keys():
            if dlg.parameter_values[parameter].text():
                parent.project.backend_parameter_set(dlg.backend, parameter, dlg.parameter_values[parameter].text())


class BackendConfigurationEditor(QDialog):
    def __init__(self, file, parent):
        super().__init__(parent)
        # win = MainEditFile(file)
        # win.setMinimumSize(600, 400)
        self.file = file

        backends_ = [backend.get('name') for backend in (etree.parse(file).xpath('//backend'))]
        self.layout = QFormLayout()
        self.edit_combo = QComboBox()
        self.edit_combo.addItem('')
        self.edit_combo.addItems(backends_)
        self.edit_combo.currentTextChanged.connect(lambda text, file=self.file: edit(text, file))
        self.layout.addRow('Edit backend', self.edit_combo)
        self.new_combo = QComboBox()
        self.new_combo.addItems(['', 'local', 'remote linux', 'Slurm', 'Other'])
        self.new_combo.currentTextChanged.connect(lambda text, file=self.file: new(text, file))
        self.layout.addRow('New backend', self.new_combo)
        self.setLayout(self.layout)


def edit(text, file):
    print('backend.edit', text, file)


def new(text, file):
    print('backend.new', text, file)
    root = etree.parse(file)
    n = etree.SubElement(root.getroot(), 'backend')
    n.set('name', 'new one')
    n.set('run_command', 'molpro')
    if text == 'remote linux':
        n.set('host', 'someone@some.computer.somewhere')
    if text == 'Slurm':
        n.set('run_command', 'your_job_submission_script')
        n.set('run_jobnumber', 'Submitted batch job *([0-9]+)')
        n.set('kill_command', 'scancel')
        n.set('status_command', 'squeue -j')
        n.set('status_running', ' (CF|CG|R|ST|S) *[0-9]')
        n.set('status_waiting', ' (PD|SE) *[0-9]')
    if text != 'local':
        n.set('cache', '.cache/sjef')
    print(etree.tostring(root))
