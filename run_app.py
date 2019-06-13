import sys

from PySide2.QtCore import QCoreApplication

from app import App


def main():
    QCoreApplication.setOrganizationName("Oleg Evseev")
    QCoreApplication.setOrganizationDomain("x3n.me")
    QCoreApplication.setApplicationName("BCI")

    app = App(sys.argv)
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
