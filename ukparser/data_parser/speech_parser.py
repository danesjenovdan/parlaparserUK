from .base_parser import BaseParser
from .utils import get_vote_key

from ..settings import API_URL, API_AUTH, API_DATE_FORMAT

from datetime import datetime
from requests.auth import HTTPBasicAuth
import requests

class SpeechParser(BaseParser):
    def __init__(self, data, reference):
        """{"date": "20.04.2018.",
        "session_ref": ["Saziv: IX, sjednica: 8"],
        "content_list": ["Prijedlog zakona o izmjenama i dopuni Zakona o prijenosu osniva\u010dkih prava nad Sveu\u010dili\u0161tem Sjever na Republiku Hrvatsku, prvo \u010ditanje, P.Z. br. 254", "Prijedlog zakona o izmjenama i dopuni Zakona o prijenosu osniva\u010dkih prava nad Sveu\u010dili\u0161tem Sjever na Republiku Hrvatsku, prvo \u010ditanje, P.Z. br. 254"],
        "speaker": ["Brki\u0107, Milijan (HDZ)"],
        "order": 1,
        "content": "Prelazimo na sljede\u0107u to\u010dku dnevnog reda, Prijedlog Zakona o izmjenama i dopuni Zakona o prijenosu osniva\u010dkih prava nad Sveu\u010dili\u0161tem Sjever na RH, prvo \u010ditanje, P.Z. br. 254.\nPredlagatelj je zastupnik kolega Robert Podolnjak na temelju \u010dlanka 85. Ustava RH i \u010dlanka 172. Poslovnika Hrvatskog sabora.\nPrigodom rasprave o ovoj to\u010dki dnevnog reda primjenjuju se odredbe Poslovnika koji se odnose na prvo \u010ditanje zakona.\nRaspravu su proveli nadle\u017eni Odbor za zakonodavstvo, nadle\u017eni Odbor za obrazovanje, znanost i kulturu.\nVlada je dostavila svoje mi\u0161ljenje.\nPozivam po\u0161tovanog kolegu gospodina Roberta Podolnjaka da nam da dodatno obrazlo\u017eenje prijedloga Zakona.\nIzvolite."},
        """
        # call init of parent object        
        super(SpeechParser, self).__init__(reference)

        self.date = data['date']

        # SPEECH

        speeches = []
        self.session = {
            "organization": self.reference.commons_id,
            "organizations": [self.reference.commons_id],
            "in_review": False,
        }

        # get and set session
        self.session['name'] = data['date']
        self.session['start_time'] = data['debate_text']
        session_id, session_status = self.add_or_get_session(data['debate_text'], self.session)

        for speech in data['speeches']:
            speaker_id = self.get_or_add_person(speech['speaker'])
            speeches.append({
                'valid_from': speech['date'].isoformat(),
                'start_time': speech['date'].isoformat(),
                'valid_to': datetime.max.isoformat(),
                'content': speech['content'],
                'order': speech['order'],
                'party': self.reference.commons_id,
                'session': session_id,
                'speaker': speaker_id,
                })

        
        self.add_speeches(speeches)