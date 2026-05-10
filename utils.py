import fitz  # PyMuPDF
from google import genai
from google.genai import types
from googleapiclient.discovery import build
from pydantic import BaseModel, Field
from typing import List, Optional
import os

class Claim(BaseModel):
    text: str = Field(description="The specific claim extracted from the text.")
    context: str = Field(description="The context surrounding the claim for better search accuracy.")
    category: str = Field(description="Category of the claim (e.g., Statistic, Financial, Date, Technical).")

class ClaimList(BaseModel):
    claims: List[Claim]

class VerificationResult(BaseModel):
    claim: str
    status: str = Field(description="One of: Verified, Inaccurate, False")
    explanation: str = Field(description="Brief explanation of why the claim was verified or flagged.")
    real_fact: Optional[str] = Field(description="The corrected fact if the claim was inaccurate or false.")
    sources: List[str] = Field(description="List of URLs used to verify the claim.")

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file using PyMuPDF."""
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_claims(text: str, api_key: str) -> List[Claim]:
    """Uses Gemini to extract verifiable claims from the text."""
    client = genai.Client(api_key=api_key)
    prompt = f"""
    Extract up to 10 specific, verifiable claims from the following text. 
    Focus on the most important statistics, dates, financial figures, and technical data.
    Provide the context for each claim to help with search accuracy.

    Text:
    {text}
    """

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ClaimList,
        ),
    )
    return response.parsed.claims[:10]


def google_search(query: str, api_key: str, engine_id: str) -> List[dict]:
    """Performs a Google Search and returns snippets and links."""
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=query, cx=engine_id, num=5).execute()
    
    results = []
    if "items" in res:
        for item in res["items"]:
            results.append({
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "link": item.get("link")
            })
    return results

def verify_claim(claim: Claim, search_results: List[dict], api_key: str) -> VerificationResult:
    """Uses Gemini to verify a claim based on search results."""
    client = genai.Client(api_key=api_key)
    
    search_context = "\n".join([
        f"Source: {r['link']}\nTitle: {r['title']}\nSnippet: {r['snippet']}\n" 
        for r in search_results
    ])
    
    prompt = f"""
    You are a professional fact-checker. Verify the following claim using the provided search results.
    
    Claim: {claim.text}
    Context from Document: {claim.context}
    
    Search Results:
    {search_context}
    
    Instructions:
    1. Classify the claim as 'Verified' (if search results confirm it), 'Inaccurate' (if search results show different data), or 'False' (if search results contradict it or no evidence is found).
    2. Provide a brief explanation.
    3. If Inaccurate or False, provide the 'real_fact' based on the search results.
    4. List the source URLs used.
    
    Be objective and strict. If no search results support the claim, mark it as False.
    """
    
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VerificationResult,
        ),
    )
    return response.parsed
