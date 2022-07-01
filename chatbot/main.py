#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tkinter as tk
from chatbot import ChatBot


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack()

        master.title('ChatBot')
        master.geometry('800x450')
        master.resizable(width=tk.FALSE, height=tk.FALSE)

        # janela de log
        self.chat_log = tk.Text(master, bd=0, bg='white', height='8', width=50, font='Arial', )
        self.chat_log.config(state=tk.DISABLED)

        # barra de rolagem
        self.scrollbar = tk.Scrollbar(master, command=self.chat_log.yview, cursor='heart')
        self.chat_log['yscrollcommand'] = self.scrollbar.set

        # botão
        self.send_button = tk.Button(master, font=('Verdana', 12, 'bold'), text='Send', width='12', height='5', bd=0,
                                     bg='#32de97', activebackground='#3c9d9b', fg='#ffffff', command=self._send)
        master.bind('<Return>', self._send)

        # entrada de texto
        self.entry_box = tk.Text(master, bd=0, bg='white', width=29, height='5', font='Arial')

        # posiciona os componentes
        self.chat_log.place(x=5, y=5, height=395, width=780)
        self.scrollbar.place(x=780, y=5, height=395)
        self.send_button.place(x=5, y=405, height=40)
        self.entry_box.place(x=143, y=405, height=40, width=652)

        # chatbot
        self.chatbot = ChatBot()

    def _send(self, e):
        msg = self.entry_box.get('1.0', 'end-1c').strip()
        self.entry_box.delete('0.0', tk.END)

        if msg != '':
            self.chat_log.config(state=tk.NORMAL)
            self.chat_log.insert(tk.END, 'Você: ' + msg + '\n\n')
            self.chat_log.config(foreground='#442265', font=('Verdana', 12))

            res = self.chatbot.chatbot_response(msg)
            self.chat_log.insert(tk.END, 'Bot: ' + res + '\n\n')

            self.chat_log.config(state=tk.DISABLED)
            self.chat_log.yview(tk.END)


root = tk.Tk()
app = App(root)
app.mainloop()
