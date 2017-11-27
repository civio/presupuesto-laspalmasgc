# -*- coding: UTF-8 -*-
from budget_app.models import *
from budget_app.loaders import SimpleBudgetLoader
from decimal import *
import csv
import os
import re

class LasPalmasGCBudgetLoader(SimpleBudgetLoader):

    def parse_item(self, filename, line):
        # Programme codes have changed in 2015, due to new laws. Since the application expects a code-programme
        # mapping to be constant over time, we are forced to amend budget data prior to 2015.
        # See https://github.com/dcabo/presupuestos-aragon/wiki/La-clasificaci%C3%B3n-funcional-en-las-Entidades-Locales
        programme_mapping = {
            # old programme: new programme
        }

        # Institutional code (all income go to the root node, and all expenses come from the root node too)
        ic_code = '000'

        # Type of data
        is_expense = (filename.find('gastos.csv')!=-1)
        is_actual = (filename.find('/ejecucion_')!=-1)

        # Expenses
        if is_expense:
            # Functional code
            # We got 5- digit functional codes as input
            fc_code = line[1].strip()

            # For 2015 we check whether we need to amend the programme code
            year = re.search('municipio/(\d+)/', filename).group(1)

            if int(year) < 2015:
                fc_code = programme_mapping.get(fc_code, fc_code)

            # Economic code
            # We got 5- digit economic codes as input, and that's ok for us
            full_ec_code = line[2].strip()

            # Concepts are the first three digits from the economic codes
            ec_code = full_ec_code[:3]

            # Item numbers are the last two digits from the economic codes (fourth and fifth digit)
            item_number = full_ec_code[-2:]

            # Description
            description = line[3].strip()

            # Parse amount
            amount = line[7 if is_actual else 4].strip()
            amount = self._parse_amount(amount)

            return {
                'is_expense': True,
                'is_actual': is_actual,
                'fc_code': fc_code,
                'ec_code': ec_code,
                'ic_code': ic_code,
                'item_number': item_number,
                'description': description,
                'amount': amount
            }

        # Income
        else:
            # Economic code
            # We got 5- digit economic codes as input and that's ok for us
            full_ec_code = line[0].strip()

            # On economic codes we get the first three digits
            ec_code = full_ec_code[:3]

            # Item numbers are the last two digits from the economic codes (fourth and fifth digit)
            item_number = full_ec_code[-2:]

            # Description
            description = line[1].strip()

            # Parse amount
            amount = line[5 if is_actual else 2].strip()
            amount = self._parse_amount(amount)

            return {
                'is_expense': False,
                'is_actual': is_actual,
                'ec_code': ec_code,
                'ic_code': ic_code,
                'item_number': item_number,
                'description': description,
                'amount': amount
            }
