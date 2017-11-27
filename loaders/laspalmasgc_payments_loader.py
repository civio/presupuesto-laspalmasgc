# -*- coding: UTF-8 -*-
from budget_app.loaders import PaymentsLoader
from budget_app.models import Budget
import re


class LasPalmasGCPaymentsLoader(PaymentsLoader):

    # Parse an input line into fields
    def parse_item(self, budget, line):
        # We got the application code
        ap_code = line[0].strip()

        # We ignore rows with incomplete data
        if not ap_code:
            return

        # We split the application code
        ap_code = ap_code.split()

        # First two digits of the programme make the policy id
        policy_id = ap_code[2][:2]
        # But what we want as area is the policy description
        policy = Budget.objects.get_all_descriptions(budget.entity)['functional'][policy_id]

        # We only get the year number, so we assign all the entries to the
        # year's last day
        date = ap_code[0]
        date = "%s-12-31" % date

        # Normalize payee data
        payee = line[3].strip()
        payee = " ".join(payee.split())
        payee = re.sub(r'^SOCIEDAD MUNICIPAL DE GESTION URBANISTICA DE LAS PALMAS DEG$', 'SOCIEDAD MUNICIPAL DE GESTION URBANISTICA DE LAS PALMAS DE GRAN CANARIA, S.A.', payee)
        payee = re.sub(r'^SALA CONTENCIOSO ADTVO DEL TRIBUNAL SUPERIOR DE JUSTICIA DE CANARIAS SECCION II$', u'TRIBUNAL SUPERIOR DE JUSTICIA DE CANARIAS SALA CONTENCIOSO ADM. SECC. 2ª', payee)
        #payee = payee.decode('utf-8', 'ignore').encode('utf-8')

        # We truncate the description to the maximum length supported in the data model
        # and fix potential enconding errors
        description = line[4].strip()[:300]
        description = " ".join(description.split())
        #description = description.decode('utf-8', 'ignore').encode('utf-8')

        # Parse amount
        amount = line[1].strip()
        amount = self._read_english_number(amount)

        return {
            'area': policy,
            'programme': None,
            'fc_code': None,  # We don't try (yet) to have foreign keys to existing records
            'ec_code': None,
            'date': date,
            'contract_type': None,
            'payee': payee,
            'anonymized': False,
            'description': description,
            'amount': amount
        }
