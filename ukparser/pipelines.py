# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from .settings import API_URL, API_AUTH
from requests.auth import HTTPBasicAuth
import requests
from ukparser.spiders.people_spider import PeopleSpider
from ukparser.spiders.content_spider import ContentSpider
from datetime import datetime

import scrapy
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem

class ImagesPipeline(ImagesPipeline):
    members = {}
    def __init__(self, *args, **kwargs):
        super(ImagesPipeline, self).__init__(*args, **kwargs)
        print('imgs pipeline getMembers')
        mps = requests.get(API_URL + 'getMPs').json()
    
        for mp in mps:
            self.members[mp['name']] = mp['id']

    def file_path(self, request, response=None, info=None):
        print("fajl path")
        print(request.meta['name'], 'file-path')
        image_guid = str(self.members[request.meta['name']]) + '.jpeg'
        print(image_guid)
        #log.msg(image_guid, level=log.DEBUG)
        return 'full/%s' % (image_guid)

    def get_media_requests(self, item, info):
        print("get media")
        yield scrapy.Request(item['image_urls'][0], meta=item)

    def item_completed(self, results, item, info):
        print("item compelte")
        print(results)
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            raise DropItem("Item contains no images")
        item['image_paths'] = image_paths
        return item


class UkparserPipeline(object):
    value = 0
    commons_id = 56
    local_data = {}
    members = {}
    parties = {}
    votes = []
    areas = {}
    
    added_debates = {}
    added_votes = {}

    debates = {}

    mandate_start_time = datetime(day=1, month=1, year=2015)

    def __init__(self):
        print('pipeline getMembers')
        mps = requests.get(API_URL + 'getMPs').json()
        for mp in mps:
            self.members[mp['name']] = mp['id']

        print('pipeline parties')
        paries = getDataFromPagerApiDRF(API_URL + 'organizations/')
        for pg in paries:
            self.parties[pg['name_parser']] = pg['id']

        print('pipeline getVotes')
        votes = getDataFromPagerApi(API_URL + 'getVotes')
        for vote in votes:
            self.votes.append(get_vote_key(vote['motion'], vote['start_time']))

        print('pipeline get districts')
        areas = getDataFromPagerApiDRF(API_URL + 'areas')
        for area in areas:
            self.areas[area['name']] = area['id']

        print('pipeline get districts')
        sessions = getDataFromPagerApiDRF(API_URL + 'sessions')
        for session in sessions:
            self.added_debates[get_vote_key(session['name'], session['start_time'])] = session['id']

    def process_item(self, item, spider):
        print(spider)

        #CONTENT PARSER
        if type(spider) == ContentSpider:
            print("spider")
            if item['type'] == 'debate':
                debate_key = get_vote_key(item['text'], item['date'].isoformat())
                if not debate_key in self.added_debates.keys():
                    print("save DEBATE MOTION VOTE")
                    # send to api and get id
                    # SESSION
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
                    debate_key = get_vote_key(item['text'], item['date'].isoformat())
                    self.debates[debate_key] = dabate_id

                    # MOTION
                    response = requests.post(API_URL + 'motions/',
                                             json={"session": dabate_id,
                                                   "text": item['text'],
                                                   "date": item['date'].isoformat(),
                                                   'party': self.commons_id},
                                             auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
                                            )
                    print(response.content)
                    motion_id = response.json()['id']

                    #VOTE
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
                else:
                    print("SKIIIIPPPPPP session")

            elif item['type'] == 'ballot':
                print("save BALLOT")
                print('process', self.value, item)
                vote_key = get_vote_key(item['text'], item['date'].isoformat())
                if not vote_key in self.votes:
                    if vote_key in self.added_votes.keys():
                        vote_id = self.added_votes[vote_key]
                        person_id = self.members[item['name']]
                        item['party'].split('(')[0].strip()
                        try:
                            party_id = self.parties[item['party'].split('(')[0].strip()]
                        except:
                            party_id = None
                        response = requests.post(API_URL + 'ballots/',
                                                 json={"option": item['option'],
                                                       "vote": vote_id,
                                                       "voter": person_id,
                                                       "voterparty": party_id},
                                                 auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
                                                )
                else:
                    print("SKIIIIPPPPPP ballots")

            # SPEECH
            elif item['type'] =='speech':
                print("save SPEECH")
                print('process', self.value, item)
                debate_text = item['debate_text']
                debate_date = item['debate_date']
                debate_key = get_vote_key(debate_text, debate_date.isoformat())
                if not debate_key in self.votes:
                    person_id = self.members[item['speaker']]
                    debate_id = self.added_debates[debate_key]
                    response = requests.post(API_URL + 'speechs/',
                                             json={"start_time": item['date'].isoformat(),
                                                   "speaker": person_id,
                                                   "content": item['content'],
                                                   "session": debate_id,
                                                   "valid_from": item['date'].isoformat(),
                                                   "valid_to": datetime.max.isoformat(),
                                                   'party': self.commons_id,
                                                   'order': item['order']},
                                             auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
                                            )
                else:
                    print("SKIIIIPPPPPP speech")

        #PEOPLE PARSER
        elif type(spider) == PeopleSpider:
            print("PPEPPEL")
            print(self.members.keys())
            if item['type'] =='mp':
                if item['name'] in self.members.keys():
                    print('pass')
                    pass
                else:
                    if item['distict'] in self.areas.keys(): 
                        area_id = self.areas[item['distict']]
                    else:
                        response = requests.post(API_URL + 'areas/',
                                             json={"name": item['distict'],
                                                   "calssification": "okraj"},
                                             auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
                                            )
                        print(response.content)
                        area_id = response.json()['id']
                        self.areas[item['distict']] = area_id
                    response = requests.post(API_URL + 'persons/',
                                             json={"name": item['name'],
                                                   "name_parser": item['name'],
                                                   "districts": [area_id]},
                                             auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
                                            )
                    print(response.content)
                    person_id = response.json()['id']
                    if item['party'] in self.parties.keys():
                        party_id = self.parties[item['party']]
                    else:
                        response = requests.post(API_URL + 'organizations/',
                                                 json={"_name": item['party'],
                                                       "name": item['party'],
                                                       "name_parser": item['party'],
                                                       "_acronym": item['party'],
                                                       "classification": "poslanska skupina"},
                                                 auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
                                                )
                        print(response.content)
                        party_id = response.json()['id']
                        self.parties[item['party']] = party_id

                    response = requests.post(API_URL + 'memberships/',
                                             json={"person": person_id,
                                                   "organization": party_id,
                                                   "role": "clan",
                                                   "label": "cl",
                                                   "start_time": self.mandate_start_time.isoformat()},
                                             auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])
                                            )
                    print(response.content)
                    motion_id = response.json()['id']




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

def getDataFromPagerApiDRF(url):
    print(url)
    data = []
    end = False
    page = 1
    while url:
        response = requests.get(url, auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])).json()
        print(response.keys())
        data += response['results']
        url = response['next']
    return data


def get_vote_key(name, date):
    return (name + date).strip()