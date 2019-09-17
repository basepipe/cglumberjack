import subprocess
import logging

def _execute(command_string):
    logging.info('Executing Command: %s' % command_string)
    p = subprocess.Popen(command_string, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    while True:
        output = p.stdout.readline()
        if output == '' and p.poll() is not None:
            break
        if output:
            print output.strip()
    rc = p.poll()
    return rc




def create_ari_xml(input_sequence, output_directory, filename, start_number):
    """
    Creates an ARRI xml file to be used in arc_cmd.  This version handles simple dpx conversion.
    :param input_sequence:
    :param output_directory:
    :param filename:
    :param start_number:
    :return:
    """
    if not start_number:
        start_number = -1


def run_arc_cmd(arri_xml):
    command_string = 'arc_cmd -c %s' % arri_xml
    p = subprocess.Popen(command_string, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    while True:
        output = p.stdout.readline()
        if output:
            print output.strip()


def create_half_res_proxy(arri_xml):
    # Read the xml file in
    # make sure the chunks of it exist that allow us to create a 1/2 res dpx sequence
    pass


def create_arri_jpg_proxy(arri_sequence, output_sequence):
    # get pre-created LUT file
    # run jpg conversion using the lut
    pass


# 1 Create the XML File
xml = r'C:\Users\tmiko\PycharmProjects\cglumberjack\src\ari_dpx_test.xml'


run_arc_cmd(xml)




