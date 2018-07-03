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

from .data_parser.session_parser import SessionParser
from .data_parser.vote_parser import BallotsParser
from .data_parser.speech_parser import SpeechParser

import scrapy
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem

COMMONS_ID = 11

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
    commons_id = COMMONS_ID
    others = 15
    local_data = {}
    members = {}
    parties = {}
    links = {}
    areas = {}
    agenda_items = {}
    orgs = {}
    
    added_session = {}
    added_votes = {}
    added_links = {}

    sessions = {}
    motions = {}
    votes = {}
    votes_dates = {}
    questions = {}
    acts = {}

    mandate_start_time = datetime(day=1, month=1, year=2015)

    def __init__(self):
        print('pipeline getMembers')
        mps = getDataFromPagerApiDRF(API_URL + 'persons')
        for mp in mps:
            self.members[mp['name_parser']] = mp['id']

        print('pipeline parties')
        print(API_URL + 'organizations/')
        paries = getDataFromPagerApiDRF(API_URL + 'organizations/')
        for pg in paries:
            self.orgs[pg['name_parser']] = pg['id']
            if pg['classification'] == 'poslanska skupina' or pg['classification'] == 'vlada' :
                self.parties[pg['name_parser']] = pg['id']

        print(self.parties)

        print('pipeline getVotes')
        votes = getDataFromPagerApiDRF(API_URL + 'votes/')
        for vote in votes:
            self.votes[get_vote_key(vote['name'], vote['start_time'])] = vote['id']
            self.votes_dates[vote['id']] = vote['start_time']

        print('pipeline get districts')
        areas = getDataFromPagerApiDRF(API_URL + 'areas')
        for area in areas:
            self.areas[area['name']] = area['id']

        print('pipeline get sessions')
        sessions = getDataFromPagerApiDRF(API_URL + 'sessions')
        for session in sessions:
            self.sessions[session['name']] = session['id']

        print('pipeline get motions')
        motions = getDataFromPagerApiDRF(API_URL + 'motions')
        for motion in motions:
            self.motions[motion['text']] = motion['id']

        print('pipeline get questions items')
        items = getDataFromPagerApiDRF(API_URL + 'questions')
        for item in items:
            self.questions[item['signature']] = item['id']

    def process_item(self, item, spider):
        print(spider)

        #CONTENT PARSER
        if type(spider) == ContentSpider:
            print("spider")
            if item['type'] == 'debate':
                #debate_key = get_vote_key(item['text'], item['date'].isoformat())
                #if not debate_key in self.added_debates.keys():
                #    print("save DEBATE MOTION VOTE")
                    # send to api and get id
                    # SESSION

                SessionParser(item, self)

            elif item['type'] == 'ballots':
                #BallotsParser(item, self)
                pass

            # SPEECH
            elif item['type'] =='speech':
                SpeechParser(item, self)


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
    url = url + '?limit=100'
    while url:
        response = requests.get(url, auth=HTTPBasicAuth(API_AUTH[0], API_AUTH[1])).json()
        print(response.keys())
        data += response['results']
        url = response['next']
    return data


def get_vote_key(name, date):
    return (name + date).strip()