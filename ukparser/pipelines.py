# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from .settings import API_URL, API_AUTH
from requests.auth import HTTPBasicAuth
import requests
#from datetime import datetime


class UkparserPipeline(object):
    value = 0
    commons_id = 12
    local_data = {}
    members = {}
    parties = {}
    votes = []
    
    added_debates = {}
    added_votes = {}
    def __init__(self):
        print('pipeline getMembers')
        mps = requests.get(API_URL + 'getMPs').json()
        for mp in mps:
            self.members[mp['name']] = mp['id']

        print('pipeline getParties')
        paries = requests.get(API_URL + 'getAllPGs/').json().values()
        for pg in paries:
            self.parties[pg['name']] = pg['id']

        print('pipeline getVotes')
        votes = getDataFromPagerApi(API_URL + 'getVotes')
        for vote in votes:
            self.votes.append(get_vote_key(vote['motion'], vote['start_time']))

    def process_item(self, item, spider):
        self.value += 1
        if item['type'] == 'debate':
            debate_key = get_vote_key(item['text'], item['date'].isoformat())
            if not debate_key in self.votes:
                print("save debate")
                # send to api and get id
                # TODO save debate/session, save motion, save vote,
                response = requests.post(API_URL + 'sessions/',
                                         json={"name": item['text'],
                                               "start_time": item['date'].isoformat(),
                                               "organization": self.commons_id,
                                               "organizations": [self.commons_id],
                                               "in_review": False,},
                                         auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
                                        )
                print(response.content)
                dabate_id = response.json()['id']

                response = requests.post(API_URL + 'motions/',
                                         json={"session": dabate_id,
                                               "text": item['text'],
                                               "date": item['date'].isoformat()},
                                         auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
                                        )
                print(response.content)
                motion_id = response.json()['id']
                response = requests.post(API_URL + 'votes/',
                                         json={"session": dabate_id,
                                               "name": item['text'],
                                               "motion": motion_id,
                                               "start_time": item['date'].isoformat(),
                                               "tags": [','],
                                               "organization": self.commons_id},
                                         auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
                                        )
                print(response.content)
                vote_id = response.json()['id']
                self.added_debates[debate_key] = dabate_id
                self.added_votes[debate_key] = vote_id
                print('process', self.value, item)

        elif item['type'] == 'ballot':
            vote_key = get_vote_key(item['text'], item['date'].isoformat())
            if vote_key in self.added_votes.keys():
                vote_id = self.added_votes[vote_key]
                person_id = self.members[item['name']]
                #party_id = self.parties[item['party']]
                #TODO save ballot
                response = requests.post(API_URL + 'ballots/',
                                         json={"option": item['option'],
                                               "vote": vote_id,
                                               "voter": person_id},
                                         auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
                                        )

        elif item['type'] =='speech':
            print('process', self.value, item)
            person_id = self.members[item['name']]
            response = requests.post(API_URL + 'speechs/',
                                     json={"start_time": item['date'].isoformat(),
                                           "speaker": person_id,
                                           "content": item['content'],
                                           "session": dabate_id,
                                           "valid_from": item['date'].isoformat(),
                                           "valid_to": datetime.max},
                                     auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
                                    )


def getDataFromPagerApi(url, per_page = None):
    data = []
    end = False
    page = 1
    while not end:
        response = requests.get(url + '?page=' + str(page) + ('&per_page='+str(per_page) if per_page else '')).json()
        data += response['data']
        if page >= response['pages']:
            break
        page += 1
    return data

def get_vote_key(name, date):
    return name + date