from django.shortcuts import render, redirect
from .forms import recipe
from app1.langchain1 import func
from rest_framework.response import Response
from rest_framework.decorators import api_view
import json
import requests
from decouple import config

pixabay_api = config('pixal_bay_api')

def get_images(query):
    params = {
        "key": pixabay_api,
        "q": f"{query} food",
        "category": "food",
        "image_type": "photo",
        "safesearch": "true",
        "per_page": 5
    }

    response = requests.get("https://pixabay.com/api/", params=params)
    if response.status_code == 200:
        data = response.json()
        for item in data.get("hits", []):
            tags = item.get("tags", "").lower()
            if not any(x in tags for x in ['live', 'animal', 'farm']):
                return item.get("webformatURL")
    
    return "https://dummyimage.com/600x400/cccccc/ffffff&text=No+Image"


# Create your views here.
@api_view(['GET','POST','PUT','PATCH','DELETE'])
def home(request):
    if request.method=='POST':
        try:
            item_name=request.data.get('required_data','').strip()
            if not item_name:
                return Response({
                    'success': False,
                    'error': 'Not valid data try with better statement'
                })
            llm_response=func(item_name)
            

            try:
               convert_to_py = [item.model_dump() for item in llm_response]

            except ValueError: 
                return Response({
                    'success': False,
                    'error': 'Not valid output from llm'
                })
            
            for item in convert_to_py:
                name=item.get("item_name")
                image_link=get_images(name)
                item['imageURL']=image_link

            request.session['save_in_session']=json.dumps(convert_to_py)
            
            return Response({
                'success': True,
                'data': convert_to_py
            })



        except Exception as e:
            return Response({
                'success': False,
                'error': f'An error  occurred: {str(e)}' 
            })
    elif request.method=='GET':
        session_data=request.session.get('save_in_session',None)
        if session_data is not None:
            try:
                convert_to_py=json.loads(session_data)

            except ValueError: 
                return Response({
                    'success': False,
                    'error': 'Not valid output from llm'
                })
            
            # for item in convert_to_py:
            #     name=item.get("item_name")
            #     image_link=get_images(name)
            #     item['imageURL']=image_link
            
            return Response({
                'success': True,
                'data': convert_to_py
            })
        else:
            return Response({'message': 'no session data found'})
