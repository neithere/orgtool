# -*- coding: utf-8 -*-

import datetime
from docu import Document, Field as f
from tool.ext import admin
from orgtool.ext.events import Event

#from activities import Action, Location
#from actors import Actor
#from contacts import Contact, PhoneNumber, EmailAddress


class Message(Event):
    sent_by = f(unicode, required=True, label=u'отправитель')
    sent_to = f(unicode, required=True, label=u'получатель')
    #date_time = f(datetime.datetime, required=True, label=u'дата и время')
    #date_time_end = f(datetime.datetime)
    #summary = f(unicode, required=True, label=u'содержание')
    #is_confirmed = f(bool)
    #activity = f(Activity, required=True)

    def __unicode__(self):
        return u'{date_time}: {sent_by} to {sent_to}'.format(**self)


#class Message(Action):
#    contact = f(Contact, required=True)


#class SMS(Action):
#    contact = f(PhoneNumber)


#class Email(Action):
#    contact = f(EmailAddress)


#class Meeting(Action):
#    location = f(Location, required=True)
