##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Button Widget Implementation"""
import zope.interface

from memphis import config, view
from memphis.form import interfaces, pagelets
from memphis.form.widget import Widget
from memphis.form.browser import widget


class ButtonWidget(widget.HTMLInputWidget, Widget):
    """A simple button of a form."""
    zope.interface.implementsOnly(interfaces.IButtonWidget)

    klass = u'button-widget'

    def update(self):
        self.value = self.field.title

        # We do not need to use the widget's update method, because it is
        # mostly about ectracting the value, which we do not need to do.
        widget.addFieldClass(self)


config.action(
    view.registerPagelet,
    pagelets.IWidgetDisplayView, interfaces.IButtonWidget,
    template=view.template("memphis.form.browser:button_display.pt"))


config.action(
    view.registerPagelet,
    pagelets.IWidgetInputView, interfaces.IButtonWidget,
    template=view.template("memphis.form.browser:button_input.pt"))
