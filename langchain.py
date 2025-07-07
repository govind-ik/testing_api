from pydantic import BaseModel,RootModel
from typing import List,Union,Optional
from langchain.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate,SystemMessagePromptTemplate,HumanMessagePromptTemplate
from decouple import config
import re
import json
from langchain_core.messages import SystemMessage,HumanMessage

class KPIs(BaseModel):
    calories_per_100g: int
    protein: Union[str, int]
    sodium: Optional[Union[str, int]] = "0"

class Sustainability(BaseModel):
    co2_impact: Optional[str] = "low"

class Items(BaseModel):
    item_name: str
    quantity: str
    estimated_price_inr: int
    kpis: KPIs
    sustainability: Sustainability

class ClassList(RootModel[List[Items]]):
    pass


def func(data):
    gem_ai=config('GEM_API_KEY')
    llm=ChatGoogleGenerativeAI(google_api_key=gem_ai,model="gemini-1.5-flash",max_tokens=800,temperature=0.2)
    parser = PydanticOutputParser(pydantic_object=ClassList)
    
    systemmsgprom=SystemMessagePromptTemplate.from_template( """You are a smart grocery assistant or a salesman who runs the shops don't output in cups quantity that can be solved in kg, gms, litres of Walmart for direct ai to cart assistance and  time-saving cart making with perfection .
Given a user's natural language request, your task is to:
1. Return ONLY a valid JSON array with one object per item
2. Do NOT include any explanation, formatting, triple quotes, or markdown
3. Do NOT write ```json or ``` anywhere in your response
4. Start directly with [ and end with ]
5. MANDATORY: Every item MUST have ALL these fields (no exceptions):
   - item_name: string (name of the item)
   - quantity: string (amount needed)
   - estimated_price_inr: number (price in INR)
   - kpis: object containing:
     * calories_per_100g: number
     * protein: string or number (grams)
     * sodium: string or number (mg)
   - sustainability: object containing:
     * co2_impact: string ("low", "med", or "high")
6. If you don't know exact values, provide reasonable estimates
7. NEVER skip any field - every item must be complete
8. Example format:
   [{"item_name": "Rice", "quantity": "1kg", "estimated_price_inr": 80, "kpis": {"calories_per_100g": 344, "protein": "8g", "sodium": "1mg"}, "sustainability": {"co2_impact": "med"}}]

CRITICAL: Your response must be ONLY valid JSON with ALL fields present in every item.
    
Keep output suitable for direct use in a frontend basket view.""")
    hummsgprom=HumanMessagePromptTemplate.from_template('{asked_dish}')

    chatpromt=ChatPromptTemplate.from_messages([systemmsgprom,hummsgprom])

    format_chat=chatpromt.format_messages(
        asked_dish=data,
        format_instructions=parser.get_format_instructions()
    )
    response=llm.invoke(format_chat)
    raw_output = response.content
    cleaned_output = clean_llm_output(raw_output)

    try:
        parsed = parser.parse(cleaned_output)
        return parsed.root
    except Exception as e:
        print(" Parsing failed:", e)
        print("Cleaned Output:", cleaned_output)
        return []
        

def clean_llm_output(raw_output: str) -> str:
   
    cleaned = raw_output.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json"):].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()
    
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    return cleaned
