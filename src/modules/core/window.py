## 
# @file window.py
# @brief Defines the main window for the application.
#
# @section file_author Author
# - Created on 07/08/2021 by Connor DeCamp
# @section mod_history Modification History
# - Modified on 10/19/2021 by Connor DeCamp
##

from PyQt5 import QtCore
from PyQt5.QtNetwork import QHostAddress
from PyQt5.QtWidgets import QAbstractScrollArea, QErrorMessage, QListWidget, \
                            QListWidgetItem, QPlainTextEdit, QTableWidgetItem, QMainWindow

                            
from modules.core.monitor_dialog import MonitorDialog
from modules.core.window_autogen import Ui_MainWindow
from modules.core.memory_map_dialog import MemoryMapDialog
from modules.network.message import MessageCode, Message, ReadRegisterMessage, bytesToMessage
from modules.network.network_threads import BroadcastThread, BroadcastWorker, TcpServerThread
from modules.network.sql_connection import SQLConnection
from modules.network.tcp_server import MyTCPServer
from modules.network.utility import DeviceType
from modules.core.sfp import SFP

from typing import Tuple
import time


class Window(QMainWindow, Ui_MainWindow):

    send_command_signal         = QtCore.pyqtSignal(object)
    kill_signal                 = QtCore.pyqtSignal(int)
    dock_discover_signal        = QtCore.pyqtSignal(str)
    cloudplug_discover_signal   = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # User-defined setup methods
        self.connectSignalSlots()

        # Allow columns to adjust to their contents
        self.tableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.verticalHeader().setVisible(False)

        self.th = QtCore.QThread()
        self.worker = BroadcastWorker()
        self.worker.moveToThread(self.th)

        self.worker.device_response.connect(self.handleUdpClientMessage)
        self.th.started.connect(self.worker.on_thread_start)
        self.kill_signal.connect(self.worker.cleanup)
        self.th.start()

        self.appendToDebugLog('Starting UDP device discovery thread')
        #udp_thread = BroadcastThread()
        #udp_thread.device_response.connect(self.handleUdpClientMessage)
        #self.kill_signal.connect(udp_thread.main_window_close_event_handler)
        #udp_thread.start()

        
        
        self.appendToDebugLog('Starting TCP server thread')
        self.tcp_server = MyTCPServer()
        self.tcp_server.client_connected_signal.connect(self.tcpClientConnectHandler)
        self.tcp_server.client_disconnected_signal.connect(self.tcpClientDisconnectHandler)
        self.tcp_server.update_ui_signal.connect(self.updateUiSignalHandler)
        self.tcp_server.log_signal.connect(self.appendToDebugLog)

        self.tcp_server.diagnostic_init_a0_signal.connect(self.handle_init_diagnostic_a0)
        self.tcp_server.diagnostic_init_a2_signal.connect(self.handle_init_diagnostic_a2)
        self.tcp_server.real_time_refresh_signal.connect(self.handle_real_time_refresh)
        self.tcp_server.remote_io_error_signal.connect(self.handle_remote_io_error)

        self.dock_discover_signal.connect(self.tcp_server.initDockConnection)
        self.cloudplug_discover_signal.connect(self.tcp_server.initCloudplugConnection)
        self.send_command_signal.connect(self.tcp_server.sendCommandSignalHandler)
        self.kill_signal.connect(self.tcp_server._close_all_connections)

        self.tcp_thread = QtCore.QThread()
        self.tcp_thread.started.connect(self.tcp_server.openSession)
        self.tcp_server.moveToThread(self.tcp_thread)
        self.tcp_thread.start()

        # It's a lot to type, so use a temp variable to access the tcp_server of the thread
        # to connect slots
        # self.tcp_server_thread = TcpServerThread()
        #self.tcp_server_thread.client_connected_signal.connect(self.tcpClientConnectHandler)
        #self.tcp_server_thread.client_disconnected_signal.connect(self.tcpClientDisconnectHandler)
        #self.tcp_server_thread.update_ui_signal.connect(self.updateUiSignalHandler)
        #self.tcp_server_thread.log_signal.connect(self.appendToDebugLog)
        #self.tcp_server_thread.diagnostic_init_a0_signal.connect(self.handle_init_diagnostic_a0)
        #self.tcp_server_thread.diagnostic_init_a2_signal.connect(self.handle_init_diagnostic_a2)
        #self.tcp_server_thread.real_time_refresh_signal.connect(self.handle_real_time_refresh)
        #self.tcp_server_thread.remote_io_error_signal.connect(self.handle_remote_io_error)

        #self.dock_discover_signal.connect(self.tcp_server_thread.initDockConnection)
        #self.cloudplug_discover_signal.connect(self.tcp_server_thread.initCloudplugConnection)

        #self.send_command_signal.connect(self.tcp_server_thread.send_command_from_ui)
        #self.kill_signal.connect(self.tcp_server_thread.main_window_close_event_handler)

        #self.tcp_server_thread.start()


        self.diagnostic_monitor_dialog = MonitorDialog(self)
        self.diagnostic_monitor_dialog.timed_command.connect(self.handle_diagnostic_timer_timeout)

    def connectSignalSlots(self):
        # Connect the 'Reprogram Cloudplugs' button to the correct callback
        self.reprogramButton.clicked.connect(self.cloudplug_reprogram_button_handler)
        self.tableWidget.doubleClicked.connect(self.display_sfp_memory_map)
        self.readSfpMemoryButton.clicked.connect(self.clone_sfp_memory_button_handler)
        self.monitorSfpButton.clicked.connect(self.display_monitor_dialog)

    def display_sfp_memory_map(self, clicked_model_index):

        # The SFP the user double clicked from the table
        selected_row_in_table = clicked_model_index.row()

        selected_sfp_id = int(self.tableWidget.item(
            selected_row_in_table, 0
        ).text())


        mydb = SQLConnection()
        mycursor = mydb.get_cursor()
        mycursor.execute(f"SELECT * FROM sfp_info.page_a0 WHERE id={selected_sfp_id};")

        page_a0 = []
        page_a2 = [0] * 256

        # should only be one result...
        for res in mycursor:
            for i in range(1, len(res)):
                page_a0.append(res[i])

        mydb.close()

        sfp = SFP(page_a0, page_a2)

        print(format(sfp.calculate_cc_base(), '02X'))
        print(sfp.get_cc_base())

        # Create SFP object after reading from database

        memory_dialog = MemoryMapDialog(self)
        memory_dialog.initializeTableValues(sfp)
        memory_dialog.show()

    def appendRowInSFPTable(self, values: Tuple) -> None:

        ID = 0
        VENDOR_ID = 1
        VENDOR_PART_NUMBER = 2
        TRANSCEIVER_TYPE = 3

        rowPosition = self.tableWidget.rowCount()        
        self.tableWidget.insertRow(rowPosition)

        self.tableWidget.setItem(rowPosition, 0, QTableWidgetItem(str(values[ID])))
        self.tableWidget.setItem(rowPosition, 1, QTableWidgetItem(values[VENDOR_ID]))
        self.tableWidget.setItem(rowPosition, 2, QTableWidgetItem(values[VENDOR_PART_NUMBER]))
        self.tableWidget.setItem(rowPosition, 3, QTableWidgetItem(values[TRANSCEIVER_TYPE]))

        self.tableWidget.resizeColumnsToContents()

    def cloudplug_reprogram_button_handler(self) -> None:
        """
        User presses this button to reprogram the selected cloudplugs with
        a single selected SFP/SFP+ persona.
        """

        # Check to see if the user has selected at least one cloudplug
        selected_cloudplugs = self.listWidget.selectedItems()
        print(f'User has selected {len(selected_cloudplugs)} cloudplugs')

        # If the user has not selected anything, show an error message and
        # return from this method
        if len(selected_cloudplugs) < 1:
            error_dialog = QErrorMessage()
            error_dialog.showMessage("You must choose at least 1 CloudPlug!")
            error_dialog.exec()
            return

        selected_sfp_persona = self.tableWidget.selectionModel().selectedIndexes()

        if len(selected_sfp_persona) == 0:
            error_dialog = QErrorMessage()
            error_dialog.showMessage("You must select an SFP from the table!")
            error_dialog.exec()
            return
        
        for model_index in selected_sfp_persona:
            print(f'{self.tableWidget.model().data(model_index) = }')


    def handleUdpClientMessage(self, contents_ip_port_tuple: Tuple):
        '''
        Handles the message from a UDP client. 
        '''
        raw_data:    bytes         = contents_ip_port_tuple[0]
        sender_ip:   QHostAddress  = contents_ip_port_tuple[1].toString()
        sender_port: int           = contents_ip_port_tuple[2]

        # DEBUG message
        # self.appendToDebugLog(f'Discovered device at {sender_ip}:{sender_port}')        
        # print(raw_data)

        received_message = bytesToMessage(raw_data)

        self.appendToDebugLog(received_message)

        if MessageCode(received_message.code) == MessageCode.DOCK_DISCOVER_ACK:
            self.appendToDebugLog(f"Discovered DOCKING STATION at {sender_ip}:{sender_port}")
            print(f"Emitting DOCK {sender_ip}")
            self.dock_discover_signal.emit(sender_ip)
        elif MessageCode(received_message.code) == MessageCode.CLOUDPLUG_DISCOVER_ACK:
            self.appendToDebugLog(f"Discovered CLOUDPLUG at {sender_ip}:{sender_port}")
            print(f"Emitting CLOUDPLUG {sender_ip}")
            self.cloudplug_discover_signal.emit(sender_ip)
        else:
            self.appendToDebugLog(f"Unknown data from {sender_ip}:{sender_port}")

    def clone_sfp_memory_button_handler(self):
        '''
        Method that handles when the "Clone SFP Memory" button is
        clicked.
        '''

        selected_item_in_dock_tab = self.dockingStationList.selectedItems()

        for ip in selected_item_in_dock_tab:
            
            # The IP address is placed as text in the list
            ip = ip.text()

            # The message code is to clone the SFP memory
            code = MessageCode.CLONE_SFP_MEMORY
            # The text of the message doesn't matter for this message
            msg = 'read the memory please and thanks'

            # The server needs to know the IP address of the client
            # and what to send to it. The only way to emit this as a
            # signal is to make it into a tuple
            msg_tuple = (ip, Message(code, msg))

            # Emits the signal with the data as the msg_tuple
            # This signal is caught by the TcpServer thread
            self.send_command_signal.emit(msg_tuple)
            

    def tcpClientConnectHandler(self, data: object):
        self.appendToDebugLog(f"Successful TCP connection from {data}")

        device_type = data[0]
        device_ip = data[1]

        if device_type == DeviceType.DOCKING_STATION:
            self.dockingStationList.addItem(QListWidgetItem(device_ip))
        elif device_type == DeviceType.CLOUDPLUG:
            self.listWidget.addItem(QListWidgetItem(device_ip))

    def tcpClientDisconnectHandler(self, data: str):
        # For each item in the list of docking stations, find its
        # row and remove it from that list.
        
        print(f"Trying to remove data from {data}")

        device_type = data[0]
        device_ip = data[1]

        if device_type == DeviceType.DOCKING_STATION:
            for item in self.dockingStationList.findItems(device_ip, QtCore.Qt.MatchExactly):
                row_of_item = self.dockingStationList.row(item)
                self.dockingStationList.takeItem(row_of_item) # removeListItem didn't work
        elif device_type == DeviceType.CLOUDPLUG:
            for item in self.listWidget.findItems(device_ip, QtCore.Qt.MatchExactly):
                row_of_item = self.listWidget.row(item)
                self.listWidget.takeItem(row_of_item)


    def updateUiSignalHandler(self, code: MessageCode):
        
        if code == MessageCode.CLONE_SFP_MEMORY_SUCCESS:
            self.appendToDebugLog("A docking station successfully, cloned SFP memory")
            self._refreshSfpTable()

    def _refreshSfpTable(self):
        sql_statement = "SELECT * FROM sfp"
        self.appendToDebugLog(f"Executing SQL STATEMENT: {sql_statement}")
        
        db = SQLConnection()

        cursor = db.get_cursor()
        cursor.execute(sql_statement)

        self.tableWidget.setRowCount(0)

        for data_tuple in cursor:
            print(data_tuple)
            self.appendRowInSFPTable(data_tuple)

        db.close()
    
        
    def display_monitor_dialog(self):
        '''! Function to display the diagnostic monitoring dialog.

            @brief If the user has selected a connected Docking Station,
            it opens a diagnostic monitoring dialog that allows the user
            to see the diagnostics of the SFP module.
        '''
        selected_items = self.dockingStationList.selectedItems()

        if len(selected_items) != 1:
            error_msg = QErrorMessage()
            if len(selected_items) > 1:
                error_msg.showMessage("You can only choose 1 Docking Station!")
            else:
                error_msg.showMessage("No Docking Stations are available!")

            error_msg.exec()
            error_msg.deleteLater()
        else:
            selected_item = selected_items[0]
            # We need to read a lot of values from the SFP before
            # we start doing diagnostic monitoring
            # Initially, we need to read:
            #   - Vendor name (16 bytes)
            #   - Part number (16 bytes)
            #   - Diagnostic Monitoring Type (1 byte)
            #   - ALL of the alarm and warning thresholds (40 or 56 bytes)

            # So we are expecting at least 73 and at most
            # 89 bytes back from the docking station

            dock_ip = selected_item.text()
            self.diagnostic_monitor_dialog.dock_ip = dock_ip

            page_a0_registers = [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
                                 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55,
                                 92]
            msg = ReadRegisterMessage(MessageCode.DIAGNOSTIC_INIT_A0, "", 0x50, page_a0_registers)
            self.send_command_signal.emit((dock_ip, msg))

            page_a2_registers = [i for i in range(91 + 1)]
            page_a2_registers += [i for i in range(96, 109 + 1)]
            msg = ReadRegisterMessage(MessageCode.DIAGNOSTIC_INIT_A2, "", 0x51, page_a2_registers)
            self.send_command_signal.emit((dock_ip, msg))

            self.diagnostic_monitor_dialog.startTimer()
            self.diagnostic_monitor_dialog.show()

    def handle_init_diagnostic_a0(self, cmd: ReadRegisterMessage):
        sfp_ptr = self.diagnostic_monitor_dialog.associated_sfp

        i = 0
        for val in cmd.register_numbers[0:16]:
            sfp_ptr.page_a0[20 + i] = val
            i += 1

        i = 0        
        for val in cmd.register_numbers[16:32]:
            sfp_ptr.page_a0[40 + i] = val
            i += 1

        diagnostic_int = cmd.register_numbers[len(cmd.register_numbers) - 1]
        sfp_ptr.page_a0[92] = diagnostic_int
        sfp_ptr.force_calibration_check()

        calibration_str = ""
        if sfp_ptr.calibration_type == SFP.CalibrationType.INTERNAL:
            calibration_str = "Internally Calibrated"
        elif sfp_ptr.calibration_type == SFP.CalibrationType.EXTERNAL:
            calibration_str = "Externally Calibrated"

        self.diagnostic_monitor_dialog.lineEdit.setText(sfp_ptr.get_vendor_name())
        self.diagnostic_monitor_dialog.lineEdit_2.setText(sfp_ptr.get_vendor_part_number())
        self.diagnostic_monitor_dialog.lineEdit_3.setText(calibration_str)
        


    def handle_init_diagnostic_a2(self, cmd: ReadRegisterMessage):
        m = self.diagnostic_monitor_dialog
        sfp_ptr = m.associated_sfp

        for i in range(91 + 1):
            sfp_ptr.page_a2[i] = cmd.register_numbers[i]

        for i in range(96, 109 + 1):
            sfp_ptr.page_a2[i] = cmd.register_numbers[i - 4]

        self.diagnostic_monitor_dialog.update_alarm_warning_tab()
        self.diagnostic_monitor_dialog.update_real_time_tab()

    def handle_diagnostic_timer_timeout(self):
        # Send a refresh real-time diagnostics message
        code = MessageCode.REAL_TIME_REFRESH
        page_num = 0x51
        # All the register numbers for diagnostic information
        registers = [96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109]

        command = ReadRegisterMessage(code, "", page_num, registers)
        self.send_command_signal.emit((self.diagnostic_monitor_dialog.dock_ip, command))

    def handle_real_time_refresh(self, cmd: ReadRegisterMessage):

        # Expecting data from registers [96, 109] in page 0x51 (aka 0xA2)
        sfp_ptr = self.diagnostic_monitor_dialog.associated_sfp
        sfp_ptr.force_calibration_check()

        for i in range(96, 109 + 1):
            sfp_ptr.page_a2[i] = cmd.register_numbers[i - 96]

        self.diagnostic_monitor_dialog.update_real_time_tab()

    def handle_remote_io_error(self, cmd: Message):
        print("Trying to close diag window")
        self.diagnostic_monitor_dialog.close()

    ##
    # Utility functions
    ##
    def closeEvent(self, event):
        print("Closing the window")

        self.kill_signal.emit(-1)
        self.tcp_thread.exit()
        self.th.exit()
        event.accept()

    def appendToDebugLog(self, text: str):
        
        text_edit = self.logTab.findChild(QPlainTextEdit, 'plainTextEdit')

        if text_edit:
            formatted_time = time.strftime('%H:%M:%S', time.localtime())
            text_edit.appendPlainText(f'[{formatted_time}]: {text}')




    