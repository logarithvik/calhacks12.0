"""
Distillation Agent - Extracts structured information from clinical trial protocols

This agent should:
1. Parse the raw protocol text
2. Extract key information:
   - Study title and phase
   - Duration and timeline
   - Inclusion/exclusion criteria
   - Study design and methodology
   - Biological mechanism
   - Expected side effects
   - Visit schedule
   - Primary and secondary endpoints
3. Return structured data in a standardized format
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai
#import PyPDF2  # Ensure this is installed
#import fitz  # PyMuPDF

class DistillAgent:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        
        genai.configure(api_key=api_key)
        # You can use gemini-1.5-flash (fast, cheap) or gemini-1.5-pro (smarter)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

        #Reads the system prompt from prompt.txt
        print(os.getcwd())
        with open("app/agents/distill_agent/prompt.txt", "r") as prompt_file:
            prompt_content = prompt_file.read()
        self.system_prompt = prompt_content

    def run(self, input_data: Dict[str, Any]):

        protocol_text = input_data.get("protocol_text", "")
        context = f"Clinical Trial Protocol Text:\n" + protocol_text

        # Adds the example output table to the context
        table_path = "app/agents/distill_agent/example_table.txt"
        context += f"\n\nHere's an example of what your output should look like:\n"
        with open(table_path, 'r') as table_file:
            table_content = table_file.read()
            context += f"\n\n{table_content}"

        try:
            # Combine system + user context
            prompt = f"{self.system_prompt}\n\nUser Query:\n{context}"

            # Generate text from Gemini
            response = self.model.generate_content(prompt)
            
            # Extract the text content from the Gemini response
            # The response object has a .text property that contains the actual generated text
            extracted_text = response.text

        except Exception as e:
            print("Error occurred while generating response:", e)
            # Return a fallback error message as plain text
            return f"Error generating summary: {str(e)}"

        return extracted_text



