#!/usr/bin/env python
import sys
import os

try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False

import sip
for api in ('QString', 'QDate', 'QDateTime', 'QTime'):
    sip.setapi(api, 2)
from PyQt4 import QtGui, QtCore

from mainwindow import Ui_MainWindow

from client import OFXConfigParser, OFXClient, VERSIONS, APPIDS, APPVERS, \
    APP_DEFAULTS, FI_DEFAULTS, STMT_DEFAULTS, ACCT_DEFAULTS, GUI_DEFAULTS
from utilities import _


class OFXGui(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self)
        # Grab the configs
        self.config = OFXConfigParser()
        self.config.read()

        # Construct the GUI from QT Designer
        self.setupUi(self)

        # Populate GUI elements
        self.setup_fi()
        self.setup_version()
        self.setup_appid()
        self.setup_appver()
        self.setup_stmt_opts()
        # Trigger fake FI selection event in order to read configs
        self.on_fi_activated(self.fi_name)

        self.connect(self.actionExit, QtCore.SIGNAL('triggered()'), QtCore.SLOT('close()'))

    def setup_fi(self):
        self.fi.addItems(self.config.fi_index)
        self.fi_name = self.fi.currentText()


    def setup_version(self):
        self.version.addItems(VERSIONS)

    def setup_appid(self):
        self.appid.addItems(APPIDS)

    def setup_appver(self):
        self.appver.addItems(APPVERS)

    def setup_stmt_opts(self):
        for (option, value) in STMT_DEFAULTS.iteritems():
            widget = getattr(self, option, None)
            if not widget:
                continue
            self.write_widget(widget, value)

    @QtCore.pyqtSlot()
    def on_actionConfig_triggered(self):
        dir =  _(os.path.join('~','.pyofx'))
        filename = QtGui.QFileDialog.getOpenFileName(self, directory=dir, filter='Configuration files (*.cfg *ini);;All files (*)')
        self.config.read(filename)

    @QtCore.pyqtSlot(str)
    def on_fi_activated(self, fi):
        """ Read configs and display to GUI widgets """
        # Store a copy for use by other object methods
        self.fi_name = fi
        for (option, value) in self.config.items(fi):
            widget = getattr(self, option, None)
            if not widget:
                continue
            self.write_widget(widget, value)


    @QtCore.pyqtSlot()
    def on_download_clicked(self):
        """ Read GUI widgets """
        # Client instance attributes
        client_opts = dict([(key, self.read_widget(getattr(self, key)))
                        for key in APP_DEFAULTS.keys() + FI_DEFAULTS.keys()])
        client = OFXClient(**client_opts)

        # Statement options
        stmt_opts = {}
        for option in STMT_DEFAULTS.keys():
            widget = getattr(self, option, None)
            stmt_opts[option] = self.read_widget(widget)

        # Account numbers
        accts = dict([(key, self.read_widget(getattr(self, key)))
                        for key in ACCT_DEFAULTS.keys()])

        client.parse_accounts(accts, **stmt_opts)
        user = self.read_widget(self.user)

        if self.dry_run.isChecked():
            request = client.write_request(user, 'TOPSECRET')
            msg = QtGui.QMessageBox(self, windowTitle='OFX Request',
                text='OFX request prepared for %s' % self.fi_name)
            msg.setDetailedText(request)
            msg.exec_()
            return

        password = self.get_password(user)

        if self.profile.isChecked():
            client.request_profile(user=user, password=password)
            archive_file = 'profile.ofx'
        else:
            client.write_request(user=user, password=password)
            # FIXME - ought to use DTCLIENT from the SONRQ here
            import datetime
            archive_file = '%s.ofx' % datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        response = client.download(user, password)
        clicked = self.popup_response(response.read())
        if clicked == QtGui.QMessageBox.Save:
            archive_dir = _(os.path.join(self.config.get('global', 'dir'), self.fi_name))
            if archive_dir == '':
                return
            if not os.path.exists(archive_dir):
                os.makedirs(archive_dir)
            archive_path = os.path.join(archive_dir, archive_file)
            archive_path = QtGui.QFileDialog.getSaveFileName(self,
                            directory=archive_path,
                            filter='OFX files (*.ofx);;All files (*)')
            with open(archive_path, 'w') as archive:
                archive.write(detail)

    def popup_response(self, detail):
        msg = QtGui.QMessageBox(self, windowTitle='OFX Response',
                text='Response received from %s' % self.fi_name,
                standardButtons=QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard)
        msg.setDefaultButton(msg.Save)
        msg.setDetailedText(detail)
        return msg.exec_()

    def read_widget(self, widget):
        if isinstance(widget, QtGui.QLineEdit):
            value = widget.text()
        elif isinstance(widget, QtGui.QComboBox):
            value = widget.currentText()
        elif isinstance(widget, QtGui.QPlainTextEdit):
            value = widget.document().toPlainText()
        elif isinstance(widget, QtGui.QCheckBox):
            value = widget.isChecked()
        elif isinstance(widget, QtGui.QDateTimeEdit):
            value = widget.dateTime().toPyDateTime()
        else:
            raise ValueError
        return value

    def write_widget(self, widget, value):
        if isinstance(widget, QtGui.QLineEdit):
            widget.setText(value)
        elif isinstance(widget, QtGui.QComboBox):
            widget.setCurrentIndex(widget.findText(value))
        elif isinstance(widget, QtGui.QPlainTextEdit):
            widget.setPlainText(value)
        elif isinstance(widget, QtGui.QCheckBox):
            widget.setChecked(value)
        elif isinstance(widget, QtGui.QDateTimeEdit):
            # FIXME
            if value is None:
                now = QtCore.QDateTime.currentDateTime()
                if widget == self.dtstart:
                    value = now.addYears(-1)
                elif widget == self.dtend:
                    value = now
                elif widget == self.dtasof:
                    value = now
                else:
                    raise ValueError
                widget.setDateTime(value)
            else:
                raise ValueError
        else:
            # FIXME
            raise ValueError

    def get_password(self, user):
        KNOW_PASSWORD = False
        if HAS_KEYRING:
            password = keyring.get_password('pyofx_%s' % self.fi_name, user)
            if password is not None:
                KNOW_PASSWORD = True
        if not KNOW_PASSWORD:
            diag = QtGui.QInputDialog
            title = 'Password'
            label = 'Password for %s' % self.fi_name
            password = None
            while password is None:
                password, ok = diag.getText(self, title, label, mode=QtGui.QLineEdit.Password)
                if ok is False: # user pressed Cancel
                    return None
                if password == '':     # user entered nothing
                    password = None
            if HAS_KEYRING:
                keyring.set_password('pyofx_%s' % self.fi_name, user, password)
        return password

def main():
    app = QtGui.QApplication(sys.argv)
    gui = OFXGui()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
