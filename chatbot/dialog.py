#!/usr/bin/env python
# -*- coding: utf-8 -*-


class State:
    def __init__(self, msg):
        self.msg = msg
        self.var = None


class Dialog:

    def __init__(self, name):
        self.name = name
        self.states = []
        self.cur = 0
        self.max = 0

    def add_state(self, msg):
        self.states.append(State(msg))
        self.max += 1

    def current(self, msg):
        if self.cur > 0:
            self.states[self.cur - 1].var = msg
        return self.states[self.cur]

    def next(self):
        self.cur += 1
        if self.cur >= self.max:
            self.restart()
            return True
        return False

    def restart(self):
        self.cur = 0


class Talk:

    def __init__(self):
        self.current_dialog = None
        self.dialogs = []

    def set_dialog(self, name):
        for dialog in self.dialogs:
            if dialog.name == name:
                self.current_dialog = dialog

    def add_dialog(self, dialog):
        self.dialogs.append(dialog)
