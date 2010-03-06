# -*- coding: utf-8 -*-

from wtforms import (
    SelectField, BooleanField, Form, PasswordField, TextField, TextAreaField, validators,
)


class GoalForm(Form):
    title = TextField('Title', [validators.required()])
    parent = SelectField('Broader goal')
    #domain = SelectField('Domain')
    summary = TextAreaField('Text')
    is_accomplished = BooleanField('Accomplished')
    is_cancelled = BooleanField('Cancelled')
