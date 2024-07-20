from tkinter import Tk
from tkinter import ttk
import tkinter as tk
from tkcalendar import DateEntry
from scr import main


params = {
    'searchString': 'Строительство Нефтебазы',
    'morphology': 'on',
    'search-filter': 'Дате размещения',
    'pageNumber': '1',
    'sortDirection': 'false',
    'strictEqual': 'false',
    'recordsPerPage': '_10',
    'showLotsInfoHidden': 'false',
    'savedSearchSettingsIdHidden': 'setting_order_lyg1m23n',
    'sortBy': 'UPDATE_DATE',
    'publishDateFrom' : '01.01.2000',
    'applSubmissionCloseDateFrom': '',
    'fz44': 'on',
    'fz223': 'on',
    'ppRf615': 'on',
    'fz94': 'on',
    'af': 'on',
    'ca': 'on',
    'pc': 'on',
    'pa': 'on',
    'priceFromGeneral': '100000000',
    'priceToGeneral': '1000000000',
    'currencyIdGeneral': '-1',
    'gws': 'Выберите тип закупки',
    'OrderPlacementSmallBusinessSubject': 'on',
    'OrderPlacementRnpData': 'on',
    'OrderPlacementExecutionRequirement': 'on',
    'orderPlacement94_0': '0',
    'orderPlacement94_1': '0',
    'orderPlacement94_2': '0',
}

def get_values():
    params['searchString'] = search_string_entry.get()
    params['morphology'] = 'on'
    params['search-filter'] = search_filter_entry.get()
    params['pageNumber'] = page_number_entry.get()
    params['sortDirection'] = 'true' if sort_direction_var.get() else 'false'
    params['strictEqual'] = 'true' if strictEqual_var.get() else 'false'
    params['recordsPerPage'] = records_per_page_entry.get()
    params['showLotsInfoHidden'] = 'true'
    params['savedSearchSettingsIdHidden'] = 'setting_order_lyg1m23n'
    params['sortBy'] = sort_options[sort_by_combobox.get()]
    params['fz44'] = 'on' if fz44_var.get() else 'off'
    params['fz223'] = 'on' if fz223_var.get() else 'off'
    params['ppRf615'] = 'on' if pprf615_var.get() else 'off'
    params['fz94'] = 'on' if fz94_var.get() else 'off'
    params['af'] = 'on' if af_var.get() else 'off'
    params['ca'] = 'on' if ca_var.get() else 'off'
    params['pc'] = 'on' if pc_var.get() else 'off'
    params['pa'] = 'on' if pa_var.get() else 'off'
    params['priceFromGeneral'] = price_from_entry.get()
    params['priceToGeneral'] = price_to_entry.get()
    params['publishDateFrom'] = publish_date_from_entry.get()
    params['applSubmissionCloseDateFrom'] = appl_submission_close_date_from_entry.get()
    params['currencyIdGeneral'] = currency_options[currency_combobox.get()]
    params['gws'] = gws_entry.get()
    params['OrderPlacementSmallBusinessSubject'] = 'on'
    params['OrderPlacementRnpData'] = 'on'
    params['OrderPlacementExecutionRequirement'] = 'on'
    params['orderPlacement94_0'] = 0
    params['orderPlacement94_1'] = 0
    params['orderPlacement94_2'] = 0
    main(params)


def logger(message):
    pass
# Создаем окно
root = Tk()
root.title("Параметры поиска")

# Создаем рамку для формы
frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

ttk.Label(frame, text="Поиск").grid(row=0, column=0, sticky=tk.W)
search_string_entry = ttk.Entry(frame, width=50)
search_string_entry.grid(row=0, column=1)
search_string_entry.insert(0, params['searchString'])

# Checkbox для morphology

# Поле для ввода search-filter
ttk.Label(frame, text="search-filter").grid(row=2, column=0, sticky=tk.W)
search_filter_entry = ttk.Entry(frame, width=50)
search_filter_entry.grid(row=2, column=1)
search_filter_entry.insert(0, params['search-filter'])

# Поле для ввода pageNumber
ttk.Label(frame, text="Номер страницы").grid(row=3, column=0, sticky=tk.W)
page_number_entry = ttk.Entry(frame, width=50)
page_number_entry.grid(row=3, column=1)
page_number_entry.insert(0, params['pageNumber'])

# Checkbox для sortDirection
sort_direction_var = tk.BooleanVar(value=params['sortDirection'] == 'true')
ttk.Checkbutton(frame, text="Сортировка от большего к меньшему", variable=sort_direction_var).grid(row=4, column=0, sticky=tk.W)

strictEqual_var = tk.BooleanVar(value=params['strictEqual'] == 'true')
ttk.Checkbutton(frame, text="Искать точно, как в запросе", variable=strictEqual_var).grid(row=4, column=1, sticky=tk.W)

# Поле для ввода recordsPerPage
ttk.Label(frame, text="Результатов на странице").grid(row=5, column=0, sticky=tk.W)
records_per_page_entry = ttk.Entry(frame, width=50)
records_per_page_entry.grid(row=5, column=1)
records_per_page_entry.insert(0, params['recordsPerPage'])

ttk.Label(frame, text="Дата публикации с:").grid(row=6, column=0, sticky=tk.W)
publish_date_from_entry = DateEntry(frame, width=47, date_pattern='dd.mm.yyyy')
publish_date_from_entry.set_date('01.01.2000')
publish_date_from_entry.grid(row=6, column=1)

# Добавление поля для ввода applSubmissionCloseDateFrom
ttk.Label(frame, text="Дата окончания подачи заявок с:").grid(row=7, column=0, sticky=tk.W)
appl_submission_close_date_from_entry = DateEntry(frame, width=47, date_pattern='dd.mm.yyyy')
appl_submission_close_date_from_entry.grid(row=7, column=1)


# Поле для ввода sortBy
ttk.Label(frame, text="Сортировать по:").grid(row=8, column=0, sticky=tk.W)
sort_options = {
    'По дате обновления': "UPDATE_DATE",
    'По дате размещения': "PUBLISH_DATE",
    'По цене': "PRICE",
    'По релевантности': "RELEVANCE"
}
sort_by_combobox = ttk.Combobox(frame, values=list(sort_options.keys()))
sort_by_combobox.grid(row=8, column=1)
sort_by_combobox.set('По дате обновления')

# Checkbox для fz44
fz44_var = tk.BooleanVar(value=params['fz44'] == 'on')
ttk.Checkbutton(frame, text="ФЗ-44", variable=fz44_var).grid(row=9, column=0, sticky=tk.W)

# Checkbox для fz223
fz223_var = tk.BooleanVar(value=params['fz223'] == 'on')
ttk.Checkbutton(frame, text="ФЗ-223", variable=fz223_var).grid(row=10, column=0, sticky=tk.W)

# Checkbox для ppRf615
pprf615_var = tk.BooleanVar(value=params['ppRf615'] == 'on')
ttk.Checkbutton(frame, text="ПП РФ 615 (Капитальный ремонт) ", variable=pprf615_var).grid(row=11, column=0, sticky=tk.W)

# Checkbox для fz94
fz94_var = tk.BooleanVar(value=params['fz94'] == 'on')
ttk.Checkbutton(frame, text="ФЗ-94", variable=fz94_var).grid(row=12, column=0, sticky=tk.W)

# Checkbox для af
af_var = tk.BooleanVar(value=params['af'] == 'on')
ttk.Checkbutton(frame, text="Подача заявок", variable=af_var).grid(row=13, column=0, sticky=tk.W)

# Checkbox для ca
ca_var = tk.BooleanVar(value=params['ca'] == 'on')
ttk.Checkbutton(frame, text="Работа комиссии", variable=ca_var).grid(row=14, column=0, sticky=tk.W)

# Checkbox для pc
pc_var = tk.BooleanVar(value=params['pc'] == 'on')
ttk.Checkbutton(frame, text="Закупка завершена", variable=pc_var).grid(row=15, column=0, sticky=tk.W)

# Checkbox для pa
pa_var = tk.BooleanVar(value=params['pa'] == 'on')
ttk.Checkbutton(frame, text="Закупка отменена", variable=pa_var).grid(row=16, column=0, sticky=tk.W)

# Поле для ввода priceFromGeneral
ttk.Label(frame, text="Начальная цена контракта (договора)").grid(row=17, column=0, sticky=tk.W)
price_from_entry = ttk.Entry(frame, width=50)
price_from_entry.grid(row=17, column=1)
price_from_entry.insert(0, params['priceFromGeneral'])

ttk.Label(frame, text="Конечная цена цена контракта (договора)").grid(row=17, column=2, sticky=tk.W)
price_to_entry = ttk.Entry(frame, width=50)
price_to_entry.grid(row=17, column=3)
price_to_entry.insert(0, params['priceToGeneral'])

# Поле для ввода currencyIdGeneral
ttk.Label(frame, text="Тип Валюты").grid(row=18, column=0, sticky=tk.W)
currency_options = {
    "Все валюты": -1,
    "Рубль": 1,
    "Доллар": 3,
    "Евро": 2
}
currency_combobox = ttk.Combobox(frame, values=list(currency_options.keys()), width=47)
currency_combobox.grid(row=18, column=1)
currency_combobox.set("Все валюты")

# Поле для ввода gws
ttk.Label(frame, text="Выберите тип закупки").grid(row=19, column=0, sticky=tk.W)
gws_entry = ttk.Entry(frame, width=50)
gws_entry.grid(row=19, column=1)
gws_entry.insert(0, params['gws'])

# Checkbox для OrderPlacementSmallBusinessSubject


# Кнопка для получения значений и печати параметров
ttk.Button(frame, text="Submit", command=get_values).grid(row=26, column=0, columnspan=2)

# Запуск основного цикла
root.mainloop()