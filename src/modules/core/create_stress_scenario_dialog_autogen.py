# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'resources/ui_files/create_stress_scenario_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(521, 175)
        self.gridLayout_3 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.label_2 = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.gridLayout_3.addWidget(self.label_2, 1, 0, 1, 1)
        self.label = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.gridLayout_3.addWidget(self.label, 0, 0, 1, 1)
        self.parameterComboBox = QtWidgets.QComboBox(Dialog)
        self.parameterComboBox.setObjectName("parameterComboBox")
        self.parameterComboBox.addItem("")
        self.parameterComboBox.addItem("")
        self.parameterComboBox.addItem("")
        self.parameterComboBox.addItem("")
        self.parameterComboBox.addItem("")
        self.gridLayout_3.addWidget(self.parameterComboBox, 0, 1, 1, 1)
        self.valuesLineEdit = QtWidgets.QLineEdit(Dialog)
        self.valuesLineEdit.setObjectName("valuesLineEdit")
        self.gridLayout_3.addWidget(self.valuesLineEdit, 2, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.gridLayout_3.addWidget(self.label_3, 2, 0, 1, 1)
        self.nameLineEdit = QtWidgets.QLineEdit(Dialog)
        self.nameLineEdit.setObjectName("nameLineEdit")
        self.gridLayout_3.addWidget(self.nameLineEdit, 1, 1, 1, 1)
        self.submitButton = QtWidgets.QPushButton(Dialog)
        self.submitButton.setObjectName("submitButton")
        self.gridLayout_3.addWidget(self.submitButton, 4, 0, 1, 2)
        self.label_4 = QtWidgets.QLabel(Dialog)
        self.label_4.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_4.setObjectName("label_4")
        self.gridLayout_3.addWidget(self.label_4, 3, 0, 1, 1)
        self.unitLabel = QtWidgets.QLabel(Dialog)
        self.unitLabel.setObjectName("unitLabel")
        self.gridLayout_3.addWidget(self.unitLabel, 3, 1, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label_2.setText(_translate("Dialog", "Scenario Name"))
        self.label.setText(_translate("Dialog", "Parameter to Modify"))
        self.parameterComboBox.setItemText(0, _translate("Dialog", "Temperature"))
        self.parameterComboBox.setItemText(1, _translate("Dialog", "VCC"))
        self.parameterComboBox.setItemText(2, _translate("Dialog", "TX Bias Current"))
        self.parameterComboBox.setItemText(3, _translate("Dialog", "RX Power"))
        self.parameterComboBox.setItemText(4, _translate("Dialog", "TX Power"))
        self.label_3.setText(_translate("Dialog", "10 Values, separated by a comma"))
        self.submitButton.setText(_translate("Dialog", "Submit"))
        self.label_4.setText(_translate("Dialog", "Values in units of:"))
        self.unitLabel.setText(_translate("Dialog", "C"))
