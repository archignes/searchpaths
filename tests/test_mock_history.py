# run: p -m pytest tests/test_mock_history.py

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extract import (
    get_history_by_week,
    get_random_search_url,
    get_search_engine_percentages,
    get_search_entry_by_datetime,
    is_guid_version_of_query
)

import show

MOCK_HISTORY = [
  {
    "title": "mock-Exa",
    "visit_count": 1,
    "last_visit_time": "2024-04-22 10:30:00",
    "url": "https://exa.ai/search?&q=artificial%20intelligence%20trends"
  },
  {
    "title": "mock-Findera",
    "visit_count": 1,
    "last_visit_time": "2024-04-21 15:45:00",
    "url": "https://www.findera.ai/"
  },
  {
    "title": "mock-AskPandi",    
    "visit_count": 1,
    "last_visit_time": "2024-04-20 09:15:00",
    "url": "https://askpandi.com/ask?q=What%20are%20the%20best%20hiking%20trails%20in%20Colorado%3F"
  },
  {
    "title": "mock-Brave",    
    "visit_count": 1,
    "last_visit_time": "2024-04-19 18:20:00",
    "url": "https://search.brave.com/search?q=online%20privacy%20tips"
  },
  {
    "title": "mock-YouChat - Research",
    "visit_count": 1,
    "last_visit_time": "2024-04-18 11:00:00",
    "url": "https://you.com/search?q=&tbm=youchat&chatMode=research"
  },
  {
    "title": "mock-YouChat - Agent",
    "visit_count": 1,
    "last_visit_time": "2024-04-17 14:30:00",
    "url": "https://you.com/search?q=&tbm=youchat&chatMode=agent"
  },
  {
    "title": "mock-YouChat - Custom",
    "visit_count": 1,
    "last_visit_time": "2024-04-16 08:45:00",
    "url": "https://you.com/search?q=&tbm=youchat&chatMode=custom"
  },
  {
    "title": "mock-Perplexity AI",    
    "visit_count": 1,
    "last_visit_time": "2024-04-15 16:10:00",
    "url": "https://www.perplexity.ai/search/?q=quantum%20computing%20breakthroughs"
  },
  {
    "title": "mock-Mojeek - RAG",
    "visit_count": 1,
    "last_visit_time": "2024-04-14 12:55:00",
    "url": "https://labs.mojeek.com/rag/search.html?q=&rid={mock_this}"
  },
  {
    "title": "mock-You.com",    
    "visit_count": 1,
    "last_visit_time": "2024-04-13 07:40:00",
    "url": "https://you.com/search?q=best%20electric%20cars%202024"
  },
  {
    "title": "mock-X (formerly Twitter)",    
    "visit_count": 1,
    "last_visit_time": "2024-04-12 19:25:00",
    "url": "https://twitter.com/search?q=%23ClimateChange"
  },
  {
    "title": "mock-ChatGPT - 3.5",
    "visit_count": 1,
    "last_visit_time": "2024-04-11 13:05:00",
    "url": "https://chat.openai.com/?model=text-davinci-002-render-sha"
  },
  {
    "title": "mock-ChatGPT - 4",
    "visit_count": 1,
    "last_visit_time": "2024-04-10 06:50:00",
    "url": "https://chat.openai.com/?model=gpt-4"
  },
  {
    "title": "mock-Bing",    
    "visit_count": 1,
    "last_visit_time": "2024-04-09 17:35:00",
    "url": "https://www.bing.com/search?q=top%20movies%20of%202023"
  },
  {
    "title": "mock-Devv",    
    "visit_count": 1,
    "last_visit_time": "2024-04-08 21:15:00",
    "url": "https://devv.ai/search/python%20machine%20learning%20tutorial"
  },
  {
    "title": "mock-DuckDuckGo",    
    "visit_count": 1,
    "last_visit_time": "2024-04-07 10:55:00",
    "url": "https://duckduckgo.com/?q=online%20privacy%20tools"
  },
  {
    "title": "mock-Microsoft Copilot",
    "visit_count": 1,
    "last_visit_time": "2024-04-06 14:40:00",
    "url": "https://copilot.microsoft.com/"
  },
  {
    "title": "mock-Ecosia",    
    "visit_count": 1,
    "last_visit_time": "2024-04-05 08:20:00",
    "url": "https://www.ecosia.org/search?q=renewable%20energy%20initiatives"
  },
  {
    "title": "mock-Andi Search",
    "visit_count": 1,
    "last_visit_time": "2024-04-04 16:05:00",
    "url": "https://andisearch.com/"
  },
  {
    "title": "mock-Marginalia Search",    
    "visit_count": 1,
    "last_visit_time": "2024-04-03 12:50:00",
    "url": "https://search.marginalia.nu/search?query=history%20of%20the%20printing%20press"
  },
  {
    "title": "mock-Perplexity AI - Pro",    
    "visit_count": 1,
    "last_visit_time": "2024-04-02 22:30:00",
    "url": "https://www.perplexity.ai/search?q=investment%20strategies%20for%20beginners&copilot=true"
  },
  {
    "title": "mock-Qwant",    
    "visit_count": 1,
    "last_visit_time": "2024-04-01 15:45:00",
    "url": "https://www.qwant.com/?q=best%20French%20restaurants%20in%20Paris"
  },
  {
    "title": "mock-YouChat",    
    "visit_count": 1,
    "last_visit_time": "2024-03-31 09:15:00",
    "url": "https://you.com/search?q=tips%20for%20better%20sleep&tbm=youchat&cfr=chat"
  },
  {
    "title": "mock-Phind Search",    
    "visit_count": 1,
    "last_visit_time": "2024-03-30 18:35:00",
    "url": "https://www.phind.com/search?q=how%20to%20start%20a%20vegetable%20garden"
  },
  {
    "title": "mock-Kagi",    
    "visit_count": 1,
    "last_visit_time": "2024-03-29 11:20:00",
    "url": "https://kagi.com/search?q=best%20productivity%20apps%202024"
  },
  {
    "title": "mock-Globe Explorer",    
    "visit_count": 1,
    "last_visit_time": "2024-03-28 14:05:00",
    "url": "https://explorer.globe.engineer/?q=%5B%22global%20warming%22,%22climate%20change%20effects%22%5D"
  },
  {
    "title": "mock-Komo",
    "visit_count": 1,
    "last_visit_time": "2024-03-27 07:50:00",
    "url": "https://komo.ai/"
  },
  {
    "title": "mock-SciPhi",    
    "visit_count": 1,
    "last_visit_time": "2024-03-26 16:30:00",
    "url": "https://search.sciphi.ai/search?q=latest%20advances%20in%20gene%20editing"
  },
  {
    "title": "mock-Cohere Coral",
    "visit_count": 1,
    "last_visit_time": "2024-03-25 13:10:00",
    "url": "https://coral.cohere.com/"
  },
  {
    "title": "mock-Tavily",
    "visit_count": 1,
    "last_visit_time": "2024-03-24 06:55:00",
    "url": "https://app.tavily.com/playground"
  },
  {
    "title": "mock-KARMA",    
    "visit_count": 1,
    "last_visit_time": "2024-03-23 19:40:00",
    "url": "https://karmasearch.org/search?q=ways%20to%20reduce%20plastic%20waste"
  },
  {
    "title": "mock-HuggingChat",
    "visit_count": 1,
    "last_visit_time": "2024-03-22 15:25:00",
    "url": "https://huggingface.co/chat/"
  },
  {
    "title": "mock-Lepton Search",
    "visit_count": 1,
    "last_visit_time": "2024-03-21 09:10:00",
    "url": "https://search.lepton.run/"
  },
  {
    "title": "mock-Cynay",    
    "visit_count": 1,
    "last_visit_time": "2024-03-20 12:00:00",
    "url": "https://cynay.com/search?q=most%20influential%20business%20leaders"
  },
  {
    "title": "mock-Morphic",
    "visit_count": 1,
    "last_visit_time": "2024-03-19 17:45:00",
    "url": "https://morphic.sh/"
  },
  {
    "title": "mock-Wikipedia",    
    "visit_count": 1,
    "last_visit_time": "2024-03-18 10:30:00",
    "url": "https://en.wikipedia.org/w/index.php?search=history%20of%20the%20Roman%20Empire"
  },
  {
    "title": "mock-Swisscows",    
    "visit_count": 1,
    "last_visit_time": "2024-03-17 21:15:00",
    "url": "https://swisscows.com/en/web?query=family-friendly%20vacation%20destinations"
  },
  {
    "title": "mock-Yandex",    
    "visit_count": 1,
    "last_visit_time": "2024-03-16 14:00:00",
    "url": "https://yandex.com/search/?text=random%20query%20ideas"
  },
  {
    "title": "mock-Yep",    
    "visit_count": 1,
    "last_visit_time": "2024-03-15 07:45:00",
    "url": "https://yep.com/web?q=sustainable%20fashion%20brands"
  },
  {
    "title": "mock-Bing Deep Search",    
    "visit_count": 1,
    "last_visit_time": "2024-03-14 16:30:00",
    "url": "https://www.bing.com/search?q=advancements%20in%20virtual%20reality%20technology&shm=cr&form=DEEPSH"
  },
  {
    "title": "mock-Wayback Machine",    
    "visit_count": 1,
    "last_visit_time": "2024-03-13 11:00:00",
    "url": "https://web.archive.org/web/*/%s"
  },
  {
    "title": "mock-Mojeek",    
    "visit_count": 1,
    "last_visit_time": "2024-03-12 19:45:00",
    "url": "https://www.mojeek.com/search?q=benefits%20of%20meditation"
  },
  {
    "title": "mock-MetaGer",    
    "visit_count": 1,
    "last_visit_time": "2024-03-11 13:30:00",
    "url": "https://metager.org/meta/meta.ger3?eingabe=top%20tourist%20attractions%20in%20Germany"
  },
  {
    "title": "mock-Startpage",    
    "visit_count": 1,
    "last_visit_time": "2024-03-10 08:15:00",
    "url": "https://www.startpage.com/do/search?q=how%20to%20improve%20your%20credit%20score"
  },
  {
    "title": "mock-Google Gemini",
    "visit_count": 1,
    "last_visit_time": "2024-03-09 17:00:00",
    "url": "https://gemini.google.com/app"
  },
  {
    "title": "mock-Stract",    
    "visit_count": 1,
    "last_visit_time": "2024-03-08 12:45:00",
    "url": "https://stract.com/search?q=introduction%20to%20data%20structures"
  },
  {
    "title": "mock-Google",    
    "visit_count": 1,
    "last_visit_time": "2024-03-07 06:30:00",
    "url": "https://www.google.com/search?q=best%20smartphone%20cameras%202024"
  },
  {
    "title": "mock-Yahoo",    
    "visit_count": 1,
    "last_visit_time": "2024-03-06 15:15:00",
    "url": "https://search.yahoo.com/search?p=top%20vacation%20destinations%202024"
  },
  {
    "title": "mock-Mwmbl",    
    "visit_count": 1,
    "last_visit_time": "2024-03-05 10:00:00",
    "url": "https://mwmbl.org/?q=open%20source%20software%20projects"
  }
]