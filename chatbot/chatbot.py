#!/usr/bin/env python
# -*- coding: utf-8 -*-
import nltk
from nltk.stem import WordNetLemmatizer
import pickle
import numpy as np
from tensorflow.keras.models import load_model
import json
import random
import requests
from datetime import datetime
from dialog import *


class ChatBot:
    ERROR_THRESHOLD = 0.80

    MODE_NORMAL = 0
    MODE_DIALOG = 1

    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()

        self.model = load_model('chatbot_model.h5')

        self.intents = json.loads(open('intents.json', encoding='utf-8').read())
        self.words = pickle.load(open('words.pkl', 'rb'))
        self.classes = pickle.load(open('classes.pkl', 'rb'))

        self.noanswers = 0

        # diálogos
        self.mode = self.MODE_NORMAL
        self.dialogs = Talk()
        # abrir ticket
        ticket_dialog = Dialog('ticket')
        ticket_dialog.add_state('Vou abrir um ticket para você.\n\n'
                          'Certo, escreva com o máximo de detalhes seu problema:')
        ticket_dialog.add_state('Qual o seu nome?')
        ticket_dialog.add_state('Qual a sua unidade consumidora?')
        ticket_dialog.add_state('Agora preciso do seu e-mail:')
        ticket_dialog.add_state('')
        # alteração de dados cadastrais
        register_dialog = Dialog('register')
        register_dialog.add_state('Certo, qual dado você gostaria de mudar?\n• Nome\n• E-mail\n• Telefone')
        register_dialog.add_state('Qual o valor você quer atribuir a este dado?')
        register_dialog.add_state('')
        # informar queda de luz
        blackout_dialog = Dialog('blackout')
        blackout_dialog.add_state('Certo, agora informe seu nome:')
        blackout_dialog.add_state('Qual a unidade consumidora?')
        blackout_dialog.add_state('Qual o horário que ocorreu a queda de energia?')
        blackout_dialog.add_state('Informe um e-mail para contato:')
        blackout_dialog.add_state('')
        # religamento de energia
        turnbackon_dialog = Dialog('turnbackon')
        turnbackon_dialog.add_state('Certo, informe seu nome:')
        turnbackon_dialog.add_state('Qual a unidade consumidora em que deseja religar?')
        turnbackon_dialog.add_state('Informe um horário de preferência para visita técnica:')
        turnbackon_dialog.add_state('Informe um e-mail para contato:')
        turnbackon_dialog.add_state('')
        self.dialogs.add_dialog(ticket_dialog)
        self.dialogs.add_dialog(register_dialog)
        self.dialogs.add_dialog(blackout_dialog)
        self.dialogs.add_dialog(turnbackon_dialog)

    def clean_up_sentence(self, sentence):
        sentence_words = nltk.word_tokenize(sentence)
        sentence_words = [self.lemmatizer.lemmatize(word.lower()) for word in sentence_words]
        return sentence_words

    def bow(self, sentence, words, show_details=True):
        sentence_words = self.clean_up_sentence(sentence)
        bag = [0] * len(words)
        for s in sentence_words:
            for i, w in enumerate(words):
                if w == s:
                    bag[i] = 1
                    if show_details:
                        print('found in bag: %s' % w)
        return np.array(bag)

    def predict_class(self, sentence, model):
        p = self.bow(sentence, self.words, show_details=False)
        res = model.predict(np.array([p]))[0]
        # np.set_printoptions(suppress=True)
        # print(res)
        results = [[i, r] for i, r in enumerate(res) if r > self.ERROR_THRESHOLD]
        results.sort(key=lambda x: x[1], reverse=True)
        return_list = []
        for r in results:
            return_list.append({'intent': self.classes[r[0]], 'probability': str(r[1])})
        return return_list

    def get_response(self, ints, intents_json, msg):
        result = None
        if len(ints) == 0 and self.mode == self.MODE_NORMAL:
            self.noanswers += 1
            if self.noanswers >= 3:
                self.noanswers = 0
                self.mode = self.MODE_DIALOG
                self.dialogs.set_dialog('ticket')
            else:
                result = 'Desculpe, não entendi. Poderia reformular a frase?'
                return result
        tag = ''
        if len(ints) > 0:
            tag = ints[0]['intent']
        list_of_intents = intents_json['intents']
        self.noanswers = 0

        if self.mode == self.MODE_NORMAL:
            for i in list_of_intents:
                if i['tag'] == tag:
                    if tag in ('ticket', 'register', 'blackout', 'turnbackon'):
                        self.mode = self.MODE_DIALOG
                        self.dialogs.set_dialog(tag)
                    elif tag == 'energy':
                        url = 'http://18.222.64.182:5000/previsao'
                        headers = {'Content-Type': 'application/json'}
                        hour = datetime.now().hour
                        data = json.dumps({'data': datetime.today().strftime('%d/%m/%Y'),
                                           'Hour': hour,
                                           'Press_mm_hg': random.randrange(720, 781),
                                           'T3': random.randrange(17, 31),
                                           'RH_3': random.randrange(28, 52)})
                        try:
                            response = requests.post(url=url, data=data, headers=headers)
                            if response.status_code == 200:
                                cons = response.text
                                cons = cons[2: 8]
                                result = 'A previsão de consumo de energia para as ' + str(hour) + ' horas é de ' + \
                                         str(cons) + 'kWh.'
                            else:
                                result = 'Parece que meus servidores estão fora do ar...\n' \
                                         'Gostaria de perguntar outra coisa?'
                        except:
                            result = 'Parece que meus servidores estão fora do ar...\n' \
                                     'Gostaria de perguntar outra coisa?'
                    else:
                        result = random.choice(i['responses'])
                    break

        if self.mode == self.MODE_DIALOG:
            result = self.dialogs.current_dialog.current(msg).msg
            if self.dialogs.current_dialog.next():
                self.mode = self.MODE_NORMAL
                if self.dialogs.current_dialog.name == 'ticket':
                    result += 'Sr(a) ' + \
                              self.dialogs.current_dialog.states[1].var + \
                              ', seu ticket foi criado com sucesso.\nEnviaremos um e-mail para '' + \
                              self.dialogs.current_dialog.states[3].var + '' assim que tivermos uma resposta.'
                elif self.dialogs.current_dialog.name == 'register':
                    result += 'Certo, o dado ' + \
                              self.dialogs.current_dialog.states[0].var + \
                              ' foi atualizado para '' + \
                              self.dialogs.current_dialog.states[1].var + '' .'
                elif self.dialogs.current_dialog.name == 'blackout':
                    result += 'Sr(a) ' + \
                              self.dialogs.current_dialog.states[0].var + \
                              ', seu incidente foi cadastrado, nossa equipe estará trabalhando para reestabelecer ' \
                              'a energia e avisaremos no e-mail'' + \
                              self.dialogs.current_dialog.states[3].var + '' assim que tivermos uma resposta.'
                elif self.dialogs.current_dialog.name == 'turnbackon':
                    result += 'Sr(a) ' + \
                              self.dialogs.current_dialog.states[0].var + \
                              ', sua solicitação foi adicionada, estaremos agendando uma visita técnica e avisaremos ' \
                              'no e-mail'' + self.dialogs.current_dialog.states[3].var + \
                              '' assim que tivermos uma resposta.'
        return result

    def chatbot_response(self, msg):
        ints = self.predict_class(msg, self.model)
        res = self.get_response(ints, self.intents, msg)
        return res
