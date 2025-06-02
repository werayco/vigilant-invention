import json
import requests
from http import HTTPStatus
import re
import streamlit as st
# from dotenv import load_dotenv
import os
from datetime import datetime


load_dotenv()
# url = os.getenv("SOEMAIL_LLM_URI")
# witai = os.getenv("WITAI")

url = st.secrets["SOEMAIL_LLM_URI"]
witai = st.secrets["WITAI"]

def test_agent(question: str):
    response = requests.get(
        json={"question": question}, url=url)
    if response.status_code == HTTPStatus.OK:
        json = response.json().get("response")
        return json


class email_event_parser:
    @staticmethod
    def classify(text):
        template = f"""You are a bot that classifies emails into categories.

        Below is the email content: 
        
        {text.strip()}

        Above is the email content.


        ## REQUIRED OUTPUT FORMAT:

        You MUST return a valid JSON response with ALL of the following fields:
        ```json
        {{
        "confidence_level": 95,
        "email_category" : " Assign a category to the email using only the following options: Personal, Work, Transactional, Promotional, Social Media, Educational, News, Events/Calendar Invites. The assigned category must be one of these options and should not exceed them."
        }}
        ```"""
        response = test_agent(question=template)
        return response

    @staticmethod
    def parse_response1(text):
            try:
                text = text.strip()
                if text.startswith('{') and text.endswith('}'):
                    return json.loads(text)
            except:
                pass
            try:
                pattern = r"```(?:json)?\s*(.*?)```"
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    return json.loads(match.group(1).strip())
                pattern = r"(\{.*\})"
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    return json.loads(match.group(1).strip())
                
                return {
                    "email_category": "unknown",
                    "confidence_level": 0}
            except Exception as e:
                return {
                    "email_category": "unknown",
                    "confidence_level": 0
                }


    @staticmethod
    def parse_response2(text):
            try:
                text = text.strip()
                if text.startswith('{') and text.endswith('}'):
                    return json.loads(text)
            except:
                pass
            try:
                pattern = r"```(?:json)?\s*(.*?)```"
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    return json.loads(match.group(1).strip())
                pattern = r"(\{.*\})"
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    return json.loads(match.group(1).strip())
     
                return {
                    "event_title": "unknown",
                    "description": "unknown",
                    "start_date": "Failed to parse email",
                    "end_date": "Failed to parse email",
                }
            except Exception as e:
                return {
                    "event_title": "unknown",
                    "description": "unknown",
                    "start_date": "Failed to parse email",
                    "end_date": "Failed to parse email",
                }
    
    @staticmethod
    def parser_prompt(email):
        prompt = f"""You are an email parser designed to extract event details from emails categorized as "Event/Calendar Invite".
        Below is the email content: 
        
        {email.strip()}

        Above is the email content.
        
        ## REQUIRED OUTPUT FORMAT:
        You MUST return a valid JSON response with ALL of the following fields:
        ```json
        {{
        "event_title": "The title or name of the event (e.g., 'Team Meeting' or 'Webinar')",
        "description": "A brief description or summary of the event's purpose or content",
        "start_date": "The starting date and time of the event, preferably in natural language (e.g., 'June 1st, 2025 at 10am'). If the email doesn't contain any start date, set it as an empty string.",
        "end_date": "The ending date and time of the event, preferably in natural language (e.g., 'June 1st, 2025 at 11am'). If the email doesn't contain any end date, but duration is mentioned, calculate the end time. Otherwise, set it as an empty string."
        }}
        ```
        """
        response = test_agent(question=prompt)
        print(response)
        return response

    @staticmethod
    def wit_ai(date_string: str):
        if date_string:
    
            headers = {
                "Authorization": f"Bearer {witai}"
            }
            data = {
                "q": date_string
            }
            response = requests.get("https://api.wit.ai/message", headers=headers, params=data)
            response = response.json()
            datetime_str = response['entities']['wit$datetime:datetime'][0]['value']
            dt = datetime.fromisoformat(datetime_str)
            return dt.strftime('%Y%m%dT%H%M%SZ')
        else:
            return ""
    
st.title("Email Categorizer and Calendar Organizer")

text_area = st.text_area("Insert the email content:")

if st.button("Categorize"):
    classify_result = email_event_parser.classify(text=text_area)
    parsed_classify = email_event_parser.parse_response1(text=classify_result)
    cat_email = parsed_classify.get("email_category", "Unknown")

    st.write(f"**Email Category:** {cat_email}")

    if cat_email == "Events/Calendar Invites":
        extract_details = email_event_parser.parser_prompt(email=text_area)
        parsed_details = email_event_parser.parse_response2(extract_details)

        event_title = parsed_details.get("event_title", "No Title Provided")
        description = parsed_details.get("description", "No Description Provided")
        start_date = parsed_details.get("start_date")
        end_date = parsed_details.get("end_date") 

        parsed_start_date = email_event_parser.wit_ai(date_string=start_date)
        parsed_end_date = email_event_parser.wit_ai(date_string=end_date)

        link = (
            f"https://www.google.com/calendar/render?action=TEMPLATE"
            f"&text={event_title}"
            f"&details={description}"
            f"&dates={parsed_start_date}/{parsed_end_date}"
        )

        st.markdown(f"### [Add to Google Calendar]({link})")
        st.write(f"**Event Title:** {event_title}")
        st.write(f"**Description:** {description}")
        st.write(f"**Start Date:** {start_date}")
        st.write(f"**Parsed StartDate:** {parsed_start_date}")
        st.write(f"**Parsed EndDate:** {parsed_end_date}")


        st.write(f"**End Date:** {end_date}")
    else:
        st.write(f"No Calender/Event detected in the email")
        st.write(parsed_classify)