"""
PyXLL Examples: Automation

PyXLL worksheet and menu functions can call back into Excel
using the Excel COM API*.

In addition to the COM API there are a few Excel functions
exposed via PyXLL that allow you to query information about
the current state of Excel without using COM.

Excel uses different security policies for different types
of functions that are registered with it. Depending on
the type of function, you may or may not be able to make
some calls to Excel.

Menu functions and macros are registered as 'commands'.
Commands are free to call back into Excel and make changes to
documents. These are equivalent to the VBA Sub routines.

Worksheet functions are registered as 'functions'. These
are limited in what they can do. You will be able to
call back into Excel to read values, but not change
anything. Most of the Excel functions exposed via PyXLL
will not work in worksheet functions. These are equivalent
to VBA Functions.

There is a third type of function - macro-sheet equivalent
functions. These are worksheet functions that are allowed to
do most things a macro function (command) would be allowed
to do. These shouldn't be used lightly as they may break
the calculation dependencies between cells if not
used carefully.

* Excel COM support was added in Office 2000. If you are
  using an earlier version these COM examples won't work.
"""

import pyxll
from pyxll import xl_menu, xl_func, xl_macro

import logging
_log = logging.getLogger(__name__)

try:
    import win32com.client
except ImportError:
    _log.warning("*** win32com.client could not be imported          ***")
    _log.warning("*** some of the automation examples will not work  ***")
    _log.warning("*** to fix this, install the pywin32 extensions.   ***")

#
# Getting the Excel COM object
#
# PyXLL has a function 'get_active_object'. This returns
# a PyIDispatch object for the Excel window instance.
# It is better to use this than
# win32com.client.Dispatch("Excel.Application")
# as it will always be the correct handle - ie the handle
# to the correct instance of Excel.
#
# The window object can be wrapped as a 
# win32com.client.Dispatch object to make it
# easier to use, as shown in these examples.
#
# For more information on win32com see the pywin32 project
# on sourceforge.
#
# The Excel object model is the same from COM as from VBA
# so usually it's straightforward to write something
# in python if you know how to do it in VBA.
#
# For more information about the Excel object model
# see MSDN or the object browser in the Excel VBA editor.
#

def xl_app():
    """returns a Dispatch object for the current Excel instance"""
    # get the Excel application object from PyXLL and wrap it
    xl_window = pyxll.get_active_object()
    xl_app = win32com.client.Dispatch(xl_window).Application

    # it's helpful to make sure the gen_py wrapper has been created
    # as otherwise things like constants and event handlers won't work.
    win32com.client.gencache.EnsureDispatch(xl_app)

    return xl_app

#
# A simple example of a menu function that modifies
# the contents of the selected range.
#

@xl_menu("win32com test", sub_menu="More Examples")
def win32com_menu_test():
    # get the current selected range and set some text
    selection = xl_app().Selection
    selection.Value = "Hello!"
    pyxll.xlcAlert("Some text has been written to the current cell")

#
# Macros can also be used to call back into Excel when
# a control is activated.
#
# These work in the same way as VBA macros, you just assign
# them to the control in Excel by name.
#

@xl_macro()
def button_example():
    xl = xl_app()
    range = xl.Range("button_output")
    range.Value = range.Value + 1

@xl_macro()
def checkbox_example():
    xl = xl_app()
    check_box = xl.ActiveSheet.CheckBoxes(xl.Caller)
    if check_box.Value == 1:
        xl.Range("checkbox_output").Value = 'CHECKED!'
    else:
        xl.Range("checkbox_output").Value = "Click the check box"

@xl_macro()
def scrollbar_example():
    xl = xl_app()
    caller = xl.Caller
    scrollbar = xl.ActiveSheet.ScrollBars(xl.Caller)
    xl.Range("scrollbar_output").Value = scrollbar.Value

#
# Worksheet functions can also call back into Excel.
#
# The function 'async_call' must be used to do the
# actual work of calling back into Excel from another
# thread, otherwise Excel may lock waiting for the function
# to complete before allowing the COM object to modify the
# sheet, which will cause a dead-lock.
#
# To be able to call xlfCaller from the worksheet function,
# the function must be declared as a macro sheet equivalent
# function by passing macro=True to xl_func.
#
# If your function modifies the Excel worksheet it will
# trigger a recalculation so you have to take care not to
# cause an infinite loop.
#
# Accessing the 'address' property of the XLCell returned
# by xlfCaller requires this function to be a macro sheet
# equivalent function.
#

@xl_func("int rows, int cols, var value", macro=True)
def automation_example(rows, cols, value):
    """copies value to a range of rows x cols below the calling cell"""

    # get the address of the calling cell using xlfCaller
    caller = pyxll.xlfCaller()
    address = caller.address

    # the update is done asynchronously so as not to block some
    # versions of Excel by updating the worksheet from a worksheet function
    def update_func():
        xl = xl_app()
        range = xl.Range(address)

        # get the cell below and expand it to rows x cols
        range = xl.Range(range.Resize(2, 1), range.Resize(rows+1, cols))

        # and set the range's value
        range.Value = value

    # kick off the asynchronous call the update function
    pyxll.async_call(update_func)

    return address

