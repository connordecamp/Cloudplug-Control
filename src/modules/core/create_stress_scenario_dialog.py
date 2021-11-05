##
# @file create_stress_secnario_dialog.py
# @brief Defines the dialog that allows users to
# create stress scenarios for an SFP.
#
# @section file_author Author
# - Created on 11/02/2021 by Connor DeCamp
# @section mod_history Modification History
# - None
##

from typing import List
from enum import Enum
from PyQt5.QtCore import pyqtSignal

from PyQt5.QtWidgets import QDialog, QErrorMessage
from modules.core.convert import temperature_bytes_to_signed_twos_complement_decimal

from modules.core.create_stress_scenario_dialog_autogen import Ui_Dialog
from modules.network.sql_connection import SQLConnection

from modules.core.convert import float_to_signed_twos_complement_bytes

class SupportedParameters(Enum):
    TEMPERATURE = 0
    VCC = 1
    TX_BIAS = 2
    RX_PWR = 3
    TX_PWR = 4

class CreateStressScenarioDialog(QDialog, Ui_Dialog):

    refresh_stress_signal = pyqtSignal(int)

    def __init__(self, parent=None, sfp_id=None):
        super().__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("Create Stress Scenario")

        self.parameterComboBox.currentIndexChanged.connect(
            self.handle_combobox_selection_change
        )

        self.submitButton.clicked.connect(
            self.handle_submit_button_clicked
        )

        self.selected_sfp_id = sfp_id


    def handle_combobox_selection_change(self, new_index) -> None:
        '''!Handler method for when the user changes their selection
        in the combobox on the page.

        @param new_index The index of the new item the user selected.
        '''
        #print(f'Parameter changed to {self.parameterComboBox.itemText(new_index)}')
        
        
        # Possible options are module temperature, voltage,
        # transmitter bias current, receiver power, transmitter
        # power. Want to tell the user what units to enter the
        # numbers in

        new_index = SupportedParameters(new_index)

        if new_index == SupportedParameters.TEMPERATURE:
            self.unitLabel.setText("C")
        elif new_index == SupportedParameters.VCC:
            self.unitLabel.setText("V")
        elif new_index == SupportedParameters.TX_BIAS:
            self.unitLabel.setText("mA")
        elif new_index == SupportedParameters.RX_PWR or new_index == SupportedParameters.TX_PWR:
            self.unitLabel.setText("mW")
        else:
            self.unitLabel.setText("ERROR")

    def handle_submit_button_clicked(self):
        # Process the entries in the values line-edit

        MAX_SCENARIO_NAME_LEN = 255
        NUM_VALUES_NEEDED = 10

        scenario_name = self.nameLineEdit.text()

        if len(scenario_name) > MAX_SCENARIO_NAME_LEN:
            e = QErrorMessage()
            e.showMessage(f'Your scenario name cannot be longer than \
                {MAX_SCENARIO_NAME_LEN} characters!'
            )
            e.exec()
            return

        value_str = self.valuesLineEdit.text()
        value_str_list = value_str.split(',')

        if len(value_str_list) != NUM_VALUES_NEEDED:
            e = QErrorMessage()
            e.showMessage(
                f"Expected {NUM_VALUES_NEEDED} values but got \
                {len(value_str_list)} instead. Check for extra commas \
                in your input!"
            )
            e.exec()
            return

        try:
            float_values = [float(val) for val in value_str_list]
        except ValueError as ve:
            e = QErrorMessage()
            e.showMessage(f"Check your formatting on the input! {ve}")
            e.exec()
            return

        byte_list = []

        selected_index = self.parameterComboBox.currentIndex()
        selected_index = SupportedParameters(selected_index)        

        if selected_index == SupportedParameters.TEMPERATURE:
            for val in float_values:
                b1, b0 = float_to_signed_twos_complement_bytes(val)
                byte_list.append(b1)
                byte_list.append(b0)

        print(byte_list)

        # Now we need to convert each value into byte format
        # This depends on the type of stress scenario the user
        # is doing. It also depends on the calibration type!
        #
        # Temperature has to go to signed twos complement int

        sql_connection = SQLConnection()
        cursor = sql_connection.get_cursor()

        query = 'INSERT INTO stress_scenarios (stress_id, sfp_id, scenario_name, `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `11`, `12`, `13`, `14`, `15`, `16`, `17`, `18`, `19`) VALUES (%s, %s, %s, '
        
        # We are inserting byte values
        NUM_BYTES = NUM_VALUES_NEEDED * 2

        for i in range(NUM_BYTES - 1):
            query += "%s, "

        query += "%s)"

        values = (0, self.selected_sfp_id, str(self.nameLineEdit.text())) + tuple(byte_list)


        print(query, values)

        cursor.execute(query, values)

        self.refresh_stress_signal.emit(self.selected_sfp_id)
        self.close()

