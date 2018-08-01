import os
import sys


def which(program):
    def is_exe(f_path):
        return os.path.isfile(f_path) and os.access(f_path, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:

        for path in os.environ["PATH"].split(os.pathsep) + ["/usr/local/bin"]:
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def main():
    pyside_rc = None
    print "RUNNING"
    qrc = """<!DOCTYPE RCC><RCC version="1.0">
    <qresource>
    """
    for dirpath, dirname, filenames in os.walk("."):
        dirpath = dirpath[2:]
        for filename in filenames:
            if not filename.endswith(".py") or filename.endswith(".qrc"):
                file_ = os.path.join(dirpath, filename)
                qrc += "    <file>%s</file>\n" % file_
    qrc += """
    </qresource>
    </RCC>
    """

    with open("lumberjack.qrc", "w") as qrc_file:
        qrc_file.write(qrc)
    if sys.platform == "win32":
        for x in sys.path:
            pyside_rc = os.path.join(x, "PySide", "pyside-rcc.exe")
            if which(pyside_rc):
                cmd ="%s -o ../src/ui/PySide_rc.py lumberjack.qrc" % pyside_rc
                print cmd
                os.system(cmd)
                break
    else:
        try:
            import PySide2
            pyside_rc = os.path.join(os.path.dirname(PySide2.__file__), "pyside2-rcc")
        except:
            print "notPyside2"
        if not pyside_rc:
            pyside_rc = which("pyside-rcc")
        else:
            pyside_rc = pyside_rc + " -py2"
        if pyside_rc:
            print "Building %s" % pyside_rc
            os.system("%s -o ../src/ui/PySide_rc.py lumberjack.qrc" % pyside_rc)

        pyqt_rc = which("pyrcc4")
        if pyqt_rc:
            print "Building pqt4 rcc"
            print """
        ******************************************************
        *             WARNING WARNING WARNING                *
        *            This is only for development            *
        *             DO NOT DISTRIBUTE THIS CODE            *
        *                 !!!!! DANGER !!!!!                 *
        ******************************************************
        """
            os.system("pyrcc4 -o ../src/ui/pyqt4_rc.py lumberjack.qrc")
        if not pyside_rc and not pyqt_rc:
            print "WTF CANT find pyside or pyqt"

if __name__ == "__main__":
    # execute only if run as a script
    main()
