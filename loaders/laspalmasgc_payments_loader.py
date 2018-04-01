# -*- coding: UTF-8 -*-
from budget_app.loaders import PaymentsLoader
from budget_app.models import Budget

import re


class PaymentsMapper:

    class CsvMapper(object):
        def __init__(self, line):
            self.__line = line

        def __getattr__(self, name):
            mapping = self._mapping

            if name not in mapping.keys():
                klass = self.__class__
                return getattr(super(klass, self), name)

            column = mapping.get(name, None)

            if column is None:
                return getattr(self, '_' + name)()

            return self._get_column(column)

        def _get_column(self, col):
            return self.__line[col].strip()

        def _date(self):
            # we only get the year number, so we assume the year's last day
            return "%s-12-31" % PaymentsMapper.year

    class CsvDefaultMapper(CsvMapper):
        _mapping = {
            'fc_code': None,
            'date': None,
            'payee': 3,
            'description': 4,
            'amount': 1
        }

        def _fc_code(self):
            # we got the application code
            ap_code = self._get_column(0)
            # the functional code is the third element in the application code,
            # if it is present
            ap_code = ap_code.split()
            return ap_code[2] if ap_code else None

    class Csv2017Mapper(CsvMapper):
        _mapping = {
            'fc_code': 1,
            'date': None,
            'payee': 5,
            'description': 6,
            'amount': 3
        }

    class Mapper(type):
        def __getitem__(self, key):
            self.year = key
            return self.mappers.get(self.year, self.CsvDefaultMapper)

    __metaclass__ = Mapper

    mappers = {
        '2017': Csv2017Mapper
    }


class LasPalmasGCPaymentsLoader(PaymentsLoader):

    # make year data available in the class and call super
    def load(self, entity, year, path):
        self.year = year
        PaymentsLoader.load(self, entity, year, path)

    # Parse an input line into fields
    def parse_item(self, budget, line):
        mapping = PaymentsMapper[self.year](line)

        fc_code = mapping.fc_code

        # We ignore rows with invalid classsification data
        if not fc_code:
            return

        # First two digits of the programme make the policy id
        policy_id = fc_code[:2]
        # But what we want as area is the policy description
        policy = Budget.objects.get_all_descriptions(budget.entity)['functional'][policy_id]

        date = mapping.date

        # Normalize payee data
        payee = mapping.payee
        payee = " ".join(payee.split())
        payee = re.sub(r'^SOCIEDAD MUNICIPAL DE GESTION URBANISTICA DE LAS PALMAS DEG$', 'SOCIEDAD MUNICIPAL DE GESTION URBANISTICA DE LAS PALMAS DE GRAN CANARIA, S.A.', payee)
        payee = re.sub(r'^SALA CONTENCIOSO ADTVO DEL TRIBUNAL SUPERIOR DE JUSTICIA DE CANARIAS SECCION II$', u'TRIBUNAL SUPERIOR DE JUSTICIA DE CANARIAS SALA CONTENCIOSO ADM. SECC. 2ª', payee)
        # We can use this to ignore encoding problems if any arise
        # payee = payee.decode('utf-8', 'ignore').encode('utf-8')

        # We truncate the description to the maximum length supported in the data model
        # and fix potential enconding errors
        description = mapping.description[:300]
        description = " ".join(description.split())
        # We can use this to ignore encoding problems if any arise
        # description = description.decode('utf-8', 'ignore').encode('utf-8')

        # Parse amount
        amount = self._read_english_number(mapping.amount)

        return {
            'area': policy,
            'programme': None,
            'fc_code': None,  # We don't try (yet) to have foreign keys to existing records
            'ec_code': None,
            'date': date,
            'payee': payee,
            'anonymized': False,
            'description': description,
            'amount': amount
        }
