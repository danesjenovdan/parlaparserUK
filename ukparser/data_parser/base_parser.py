from .utils import fix_name, name_parser

from ..settings import API_URL, API_AUTH

from requests.auth import HTTPBasicAuth

import requests
import editdistance

class BaseParser(object):
    def __init__(self, reference):
        self.reference = reference

    # TODO
    def api_request(self, endpoint, dict_key, value_key, json_data):
        if value_key in getattr(self.reference, dict_key).keys():
            obj_id = getattr(self.reference, dict_key)[value_key]
            return obj_id, 'get'
        else:
            response = requests.post(
                API_URL + endpoint,
                json=json_data,
                auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
            )
            try:
                obj_id = response.json()['id']
                getattr(self.reference, dict_key)[value_key] = obj_id
            except Exception as e:
                print(endpoint, e, response.text)
                return None, 'fail'
        return obj_id, 'set'


    def get_agenda_item(self, value_key, json_data):
        return self.api_request('agenda-items/', 'agenda_items', value_key, json_data)


    def get_or_add_person(self, name, districts=None, mandates=None, education=None, birth_date=None):
        person_id = self.get_person_id(name)
        if not person_id:
            person_data = {
                'name': fix_name(name),
                'name_parser': name_parser(name),
            }
            if districts:
                person_data['districts'] = districts
            if mandates:
                person_data['mandates'] = mandates
            if education:
                person_data['education'] = education
            if birth_date:
                person_data['birth_date'] = birth_date
            print('Adding person', person_data)
            response = requests.post(
                API_URL + 'persons/',
                json=person_data,
                auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
            )
            print("NEWWW PERSON  check it: ", name)
            try:
                person_id = response.json()['id']
                self.reference.members[name] = person_id
            except Exception as e:
                print(e, response.json())
                return None
        return person_id

    def get_person_id(self, name):
        for key in self.reference.members.keys():
            for parser_name in key.split(','):
                if editdistance.eval(name, parser_name) < 1:
                    return self.reference.members[key]
        return None

    def add_or_get_motion(self, value_key, json_data):
        return self.api_request('motions/', 'motions', value_key, json_data)

    def add_or_get_area(self, value_key, json_data):
        return self.api_request('areas/', 'areas', value_key, json_data)

    def add_or_get_vote(self, value_key, json_data):
        return  self.api_request('votes/', 'votes', value_key, json_data)

    def add_or_get_question(self, value_key, json_data):
        return  self.api_request('questions/', 'questions', value_key, json_data)

    def add_link(self, json_data):
        n_item = len(getattr(self.reference, 'links'))
        return  self.api_request('links/', 'links', str(n_item+1), json_data)

    def add_ballot(self, voter, vote, option, party=None):
        json_data ={
            'option': option,
            'vote': vote,
            'voter': voter,
            'voterparty': self.reference.others
        }
        if party:
            json_data.update({"voterparty": party})
        response = requests.post(
            API_URL + 'ballots/',
            json=json_data,
            auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
        )
        print(response.text)

    def add_ballots(self, json_data):
        print("SENDING BALLOTS")
        response = requests.post(
            API_URL + 'ballots/',
            json=json_data,
            auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
        )

    def add_speeches(self, json_data):
        print("SENDING SPEECHES")
        response = requests.post(
            API_URL + 'speechs/',
            json=json_data,
            auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
        )

    def add_or_get_session(self, session_name, json_data):
        return  self.api_request('sessions/', 'sessions', session_name, json_data)

    def parse_edoc_person(self, data):
        splited = data.split('(')
        print(splited)
        name = splited[0]
        if len(splited) > 1:
            pg = splited[1].split(')')[0]
            print(pg)
        else:
            # ministers names are splited with /
            splited = data.split('/')
            if len(splited) > 1:
                name = splited[0]
                pg = splited[1].strip()
                if ';' in pg:
                    pg = pg.replace(';', '')
                if 'Vlade' in pg:
                    pg = 'vlada'
            else:
                pg = None
        name = ' '.join(reversed(list(map(str.strip, name.split(',')))))
        return name, pg

    def get_organization_id(self, name):
        p = False
        #if 'mora' in name:
        #    p = True
        for key in self.reference.parties.keys():
            for parser_name in key.split('|'):
                #if p:
                #    print(parser_name, editdistance.eval(name, parser_name))
                if editdistance.eval(name, parser_name) < 1:
                    return self.reference.parties[key]
        return None

    def add_organization(self, name, classification, create_if_not_exist=True):
        party_id = self.get_organization_id(name)

        if not party_id:
            if create_if_not_exist:
                print("ADDING ORG " + name)
                response = requests.post(API_URL + 'organizations/',
                                         json={"_name": name.strip(),
                                               "name": name.strip(),
                                               "name_parser": name.strip(),
                                               "_acronym": name[:100],
                                               "classification": classification},
                                         auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
                                        )
                
                try:
                    party_id = response.json()['id']
                    self.reference.parties[name.strip()] = party_id
                except Exception as e:
                    print(e, response.json())
                    return None
            else:
                return None

        return party_id

    def add_membership(self, person_id, party_id, role, label, start_time):
        response = requests.post(API_URL + 'memberships/',
                                 json={"person": person_id,
                                       "organization": party_id,
                                       "role": role,
                                       "label": label,
                                       "start_time": start_time},
                                 auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
                                )
        membership_id = response.json()['id']
        return membership_id
