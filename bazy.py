import datetime
import sqlite3 as sq
import numpy as np
from Crypto.PublicKey import RSA
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.button import MDFlatButton, MDRoundFlatButton
from kivymd.uix.dialog import MDDialog
import pandas as pd
from kivymd.uix.picker import MDTimePicker, MDDatePicker
from kivy.lang import Builder
from kivy.properties import StringProperty, ListProperty
from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineIconListItem, MDList
from kivymd.uix.datatables import MDDataTable
from kivymd.effects.stiffscroll import StiffScrollEffect


class Pierwszy(Screen):
    pass


class Drugi(Screen):
    pass


class Menedzer(ScreenManager):
    pass


class ContentNavigationDrawer(MDBoxLayout):
    pass


class ItemDrawer(OneLineIconListItem):
    icon = StringProperty()
    text_color = ListProperty((1, 1, 1, 1))


class DrawerList(ThemableBehavior, MDList):
    def set_color_item(self, instance_item):
        for item in self.children:
            if item.text_color == self.theme_cls.primary_color:
                item.text_color = self.theme_cls.text_color
                break
        instance_item.text_color = self.theme_cls.primary_color


class Content(BoxLayout):
    pass


class Kalendarz(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        self.conn = sq.connect('baza.db')
        self.c = self.conn.cursor()
        return Builder.load_file('time.kv')

    def kalendarz(self, poczatek, koniec):
        self.c.execute("""SELECT ROW_NUMBER() OVER(ORDER BY L.Dzien ASC),K.Imie ||' ' ||K.Nazwisko AS uczen,K.Poziom,L.Dzien
                                           ,L.godzina_rozp
                                           ,L.godzin_zakon,L.status FROM Lekcje AS L JOIN Klienci AS K ON K.klienci_id=L.klienci_id WHERE K.mentor_id=:men AND L.Dzien BETWEEN
                                           :dzien AND :koniec """,
                       {'men': self.mentor_id, 'dzien': poczatek, 'koniec': koniec})

    def wynagrodzenie(self, poczatek, koniec):
        sql = """SELECT  L.trwanie,K.Poziom FROM Lekcje AS L JOIN KLIENCI AS K ON K.klienci_id=L.klienci_id 
            WHERE K.mentor_id=:men_id AND L.Dzien BETWEEN :pocz AND :kon
                """
        self.c.execute(sql, {'men_id': self.mentor_id, 'pocz': poczatek, 'kon': koniec})

    def dodaj_uzytkownika(self):
        self.dialog4 = MDDialog(
            title="Dane nowego użytkownika:",
            type="custom",
            content_cls=Content(),
            buttons=[
                MDFlatButton(
                    text="Zapisz", text_color=self.theme_cls.primary_color, on_release=self.zapisz_uzytkownika
                ),
            ],
        )
        self.dialog4.open()

    def zapisz_uzytkownika(self, *args):

        imie_uzyt = self.dialog4.content_cls.ids.imie_uzyt.text
        naz_uzyt = self.dialog4.content_cls.ids.nazw_uzyt.text
        log = self.dialog4.content_cls.ids.login_uzyt.text
        has = self.dialog4.content_cls.ids.haslo_uzyt.text
        x = list(has.encode('ascii'))
        y = [x[i] * 128 ** (len(x) - i) for i in range(len(x))]
        with open('rsa_jey.bin', 'rb') as file:
            key = RSA.import_key(file.read(), passphrase="Unguessable")
        haslo = hex(pow(sum(y), key.e, key.n))
        przed = self.dialog4.content_cls.ids.przed_uzyt.text
        self.c.execute("SELECT * FROM Mentorzy WHERE login=:log", {'log': log})
        odp = self.c.fetchall()
        if "" not in [imie_uzyt, naz_uzyt, log, haslo, przed] and len(odp) == 0:
            self.c.execute(""" INSERT INTO Mentorzy(first_name, last_name, przedmiot , login , haslo ) VALUES (:imie,:nazw,:przed,:log,:has)
         """, {'imie': imie_uzyt, 'nazw': naz_uzyt, 'przed': przed, 'log': log, 'has': haslo})
            self.conn.commit()
            MDDialog(text="Dodano").open()
            self.dialog4.dismiss(force=True)
        elif len(odp) != 0:
            MDDialog(text="Podany login już istnieje").open()

    def zaloguj(self):
        has = self.root.ids.haslo.text
        x = list(has.encode('ascii'))
        y = [x[i] * 128 ** (len(x) - i) for i in range(len(x))]
        with open('rsa_jey.bin', 'rb') as file:
            key = RSA.import_key(file.read(), passphrase="Unguessable")
        haslo = hex(pow(sum(y), key.e, key.n))
        self.c.execute(""" SELECT mentor_id,login,haslo FROM Mentorzy WHERE login=:log AND haslo=:has
""", {'log': self.root.ids.login.text, 'has': haslo})
        logowanie = self.c.fetchall()
        if len(logowanie) != 0:
            self.mentor_id = logowanie[0][0]
            self.root.ids.manager.current = "Kalendarz"
            self.x = datetime.datetime.today().date()
            self.y = self.x + datetime.timedelta(days=6 - self.x.weekday())
            z = self.x - datetime.timedelta(days=self.x.weekday())
            self.kalendarz(self.x, self.y)
            dane = self.c.fetchall()

            if len(dane) == 1:
                dane.append(("", "", "", "", "", "", ""))
            self.table = MDDataTable(
                size_hint=(1, 0.6),
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                column_data=[
                    ("Lp.", dp(10)),
                    ("Uczeń", dp(30)),
                    ("Poziom", dp(20)),
                    ("Data", dp(30)),
                    ("Godzina rozpoczęcia", dp(20)),
                    ("Godzina zakończenia", dp(20)),
                    ("Status", dp(30)),
                ],
                row_data=dane,
                use_pagination=True,
                rows_num=7,
                pagination_menu_height='240dp',
                pagination_menu_pos="auto"
            )
            self.table.bind(on_row_press=self.edycja)
            self.root.ids.tool.add_widget(self.table)
            self.table2 = MDDataTable(
                size_hint=(0.7, 0.6),
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                column_data=[
                    ("Liczba godzin PP", dp(30)),
                    ("Liczba godzin R", dp(30)),
                    ("Liczba godzin ST", dp(30)),
                    ("Łączna liczba godzin", dp(40)),
                    ("Wynagrodzenie", dp(30)),
                ],
            )
            self.root.ids.summary.add_widget(self.table2)
            self.get_date3(instance=None, time=None, date=[z, self.x])
        else:
            MDDialog(text="Niepoprawne dane logowania").open()

    def edycja_lekcji(self, *args):
        MDDialog(text="Wybierz zdarzenie do edycji", buttons=[MDFlatButton(text="Godzina"),
                                                              MDFlatButton(text="Status")]).open()

    def usuwanie_lekcji(self, *args):
        MDDialog(text="Wybierz opcję", buttons=[MDFlatButton(text="Usuń tą lekcję"),
                                                MDFlatButton(text="Usuń wszystkie lekcje z tym uczniem")]).open()

    def edycja(self, table, row):
        try:
            self.row = int(row.text)
            self.dialog3 = MDDialog(text="Wybierz opcje",
                                    buttons=[MDFlatButton(text="Edytuj", on_release=self.edycja_lekcji),
                                             MDFlatButton(text="Usuń", on_release=self.usuwanie_lekcji)])
            self.dialog3.open()
        except:
            MDDialog(text="Wybrano niepoprawną kolumnę").open()

    def Zmien_ekran(self, da):
        self.root.ids.nav_drawer.set_state("close")
        self.root.ids.manager.current = da.text

    def on_start(self):
        icons_item = {
            "calendar": "Kalendarz",
            "account-multiple-plus": "Dodaj nowego ucznia",
            "sigma": "Podsumowanie"

        }
        for icon_name in icons_item.keys():
            self.root.ids.content_drawer.ids.md_list.add_widget(
                ItemDrawer(icon=icon_name, text=icons_item[icon_name], on_release=self.Zmien_ekran)
            )

    def zapisz_ucznia(self):
        # print(self.root.ids)
        imie = self.root.ids.imie.text
        nazw = self.root.ids.nazwisko.text
        poziom = ""
        data = self.root.ids.date_label.text
        rozp = self.root.ids.time_label.text
        zak = self.root.ids.time_label2.text
        status = self.root.ids.status_tekst.text
        powtor = self.root.ids.liczba_dni.text
        probna = self.root.ids.probna.active

        if self.root.ids.pp.active:
            poziom = "PP"
        elif self.root.ids.r.active:
            poziom = "R"
        elif self.root.ids.st.active:
            poziom = "ST"
        if not "" in [imie, nazw, poziom, data, rozp, zak, status]:
            self.c.execute(""" INSERT INTO Klienci(Imie ,Nazwisko,mentor_id,Poziom)
            VALUES (:imie,:naz,:men_id,:poz)
            """, {'imie': imie, 'naz': nazw, 'men_id': self.mentor_id, 'poz': poziom})
            self.conn.commit()
            u = 365
            if powtor:
                u = int(self.root.ids.liczba_dni.text)
            t = 365 // u
            b = datetime.datetime.strptime(rozp, '%H:%M').time()
            c = datetime.datetime.strptime(zak, '%H:%M').time()
            b1 = datetime.timedelta(seconds=b.hour * 3600 + b.minute * 60)
            c1 = datetime.timedelta(seconds=c.hour * 3600 + c.minute * 60)
            delta = (c1 - b1)
            uczen_id = self.c.lastrowid
            for i in range(0, t):
                self.c.execute(""" INSERT INTO Lekcje(klienci_id,Dzien ,godzina_rozp ,godzin_zakon ,trwanie,Lekcja_probna,status)
                VALUES (:kl_id,:dz,:roz,:zak,:trw,:prob,:st)
            """, {'kl_id': uczen_id,
                  'dz': datetime.datetime.strptime(data, '%d.%m.%Y').date() + datetime.timedelta(days=i * u),
                  'roz': rozp, 'zak': zak, 'trw': delta.seconds / 3600, 'prob': str(probna)[0], 'st': status})
                self.conn.commit()
            self.clearing()
            self.kalendarz(self.x, self.y)
            dane = self.c.fetchall()
            if len(dane) == 1:
                dane.append(("", "", "", "", "", "", ""))
            self.table.row_data = dane
        else:
            self.dialog = MDDialog(text="Wprowadź pełne dane",
                                   buttons=[MDFlatButton(text="OK", on_release=self.dialog_close)])
            self.dialog.open()

    def dodaj_status(self):
        self.dialog2 = MDDialog(text="Wybierz status",
                                buttons=[MDRoundFlatButton(text="Zaplanowana", on_release=self.dialog_status),
                                         MDRoundFlatButton(text="Potwierdzona", on_release=self.dialog_status)])
        self.dialog2.open()

    def dialog_status(self, *args):
        self.root.ids.status_tekst.text = args[0].text
        self.dialog2.dismiss(force=True)

    def dialog_close(self, *args):
        self.dialog.dismiss(force=True)

    def clearing(self):
        self.root.ids.imie.text = ""
        self.root.ids.nazwisko.text = ""
        self.root.ids.powtarza.active = False
        self.root.ids.time_label.text = ""
        self.root.ids.time_label2.text = ""
        self.root.ids.date_label.text = ""
        self.root.ids.probna.active = False
        self.root.ids.liczba_dni.text = ""
        self.root.ids.status_tekst.text = ""
        self.root.ids.r.active = False
        self.root.ids.pp.active = False
        self.root.ids.st.active = False

    def clearing2(self):
        self.root.ids.time_label.text = ""
        self.root.ids.time_label2.text = ""
        self.root.ids.date_label.text = ""

    def get_date(self, instance, time, date):
        self.root.ids.date_label.text += str(time.__format__('%d.%m.%Y'))

    def get_date2(self, instance, time, date):
        self.x = date[0]
        self.y = date[-1]
        self.kalendarz(date[0], date[-1])
        dane = self.c.fetchall()
        if len(dane) == 1:
            dane.append(("", "", "", "", "", "", ""))
        self.table.row_data = dane

    def check(self, tab, slowo, df):
        if slowo in df.index:
            tab.append(df.loc[slowo, 'Trwanie'])
        else:
            tab.append(0)

    def get_date3(self, instance, time, date):
        self.wynagrodzenie(date[0], date[-1])
        dane = self.c.fetchall()
        df = pd.DataFrame(data=dane, columns=['Trwanie', 'Poziom'])
        staw = pd.DataFrame(index=['PP', 'R', 'ST'], data=[40, 45, 50], columns=['Stawka'])
        df2 = df.join(staw, on='Poziom')
        df2['Total'] = df2['Trwanie'] * df2['Stawka']
        gr = df2.groupby('Poziom')
        obliczone = gr.sum()
        if 'Total' not in obliczone.keys():
            obliczone['Total'] = 0
        row = []
        self.check(row, 'PP', obliczone)
        self.check(row, 'R', obliczone)
        self.check(row, 'ST', obliczone)
        row.append(sum(row))
        row.append(format(obliczone['Total'].sum(), '.2f') + ' zł')
        row = [tuple(row), ("", "", "", "", "")]
        self.table2.row_data = row

    def show_date(self):
        data = MDDatePicker()
        data.bind(on_save=self.get_date)
        data.open()

    def show_date2(self):
        data = MDDatePicker(mode="range")
        data.bind(on_save=self.get_date2)
        data.open()

    def show_date3(self):
        data = MDDatePicker(mode="range")
        data.bind(on_save=self.get_date3)
        data.open()

    def get_time(self, instance, time):
        if self.root.ids.time_label.text == "":
            self.root.ids.time_label.text += str(time.__format__('%H:%M'))
            if self.root.ids.probna.active:
                delta = (datetime.timedelta(hours=time.hour, minutes=time.minute) + datetime.timedelta(minutes=30))
                hour = delta.seconds // 3600
                sec = delta.seconds
                sec -= hour * 3600
                minut = sec // 60
                self.root.ids.time_label2.text += \
                    str(datetime.time(hour=hour, minute=minut).__format__('%H:%M'))
        elif self.root.ids.time_label2.text == "":
            self.root.ids.time_label2.text += str(time.__format__('%H:%M'))

    def show_time(self):
        default = datetime.datetime.now().time()
        timepic = MDTimePicker()
        if default > datetime.time(hour=12):
            timepic.am_pm = 'pm'
        timepic.set_time(default)
        timepic.bind(on_save=self.get_time)
        timepic.open()


Kalendarz().run()
