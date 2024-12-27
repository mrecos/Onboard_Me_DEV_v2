from flask import Flask, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import psycopg2
import logging
from datetime import datetime
import time


# from openai import OpenAI     # for openAI assistant
import openai 
import os                     # for env variables
import json                   # for json
from datetime import datetime # for timestamp
from time import sleep        # for sleep
import time 
# import sqlite3                # for database
import re                     # for regex
from json import dumps        # for json dumps
from json import loads        # for json loads
import pandas as pd # for data processing
from pydantic import ValidationError # for pydantic validation error
from typing import List
import collections  

#added 9/6
import psycopg2
import logging
logging.basicConfig(level=logging.DEBUG)

# langchain imports
from langchain_core.output_parsers import JsonOutputParser # for parsing output
from langchain.prompts import PromptTemplate # for prompt template to contain parser
from langchain_openai import ChatOpenAI # for chat openAI authentification/connection
from langchain_core.pydantic_v1 import BaseModel, Field # for pydantic (supports output parser)
from langchain.chains import LLMChain # for LLMChain
# from langchain.memory import ChatMessageHistory # for chat message history
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder # for chat prompt template
from langchain.memory import ConversationBufferMemory # for conversation summary memory
from langchain.callbacks.tracers.run_collector import RunCollectorCallbackHandler # for run collector
from langchain_core.callbacks import StdOutCallbackHandler # for callback handler
from langchain_core.messages import SystemMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.output_parsers import PydanticOutputParser
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Global variables
log_messages = []
llm_outputs = []
# Initialize limiter without app
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["300 per day", "100 per hour"]
)


# Authentification for OpenAI
def openAI_auth():
    try:
        chat = ChatOpenAI(model="gpt-4o", 
                          temperature=0.2, 
                          openai_api_key="sk-proj-BGaO1vushEqRhLBS7vnIT3BlbkFJxH0UiStvsF7tJm4Yctg8")
        return chat
    except Exception as e:
        print(e)
        return(e)
    
# authentification for OpenAI
chat = openAI_auth()

# def create_limiter(app):
#     limiter = Limiter(
#         app=app,
#         key_func=get_remote_address,
#         default_limits=["5 per minute"],
#         storage_uri="memory://"
#     )
#     return limiter

def add_log(message):
    """Append a log message with a timestamp to the global list."""
    import time
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    entry = f"[{timestamp}] {message}"
    log_messages.append(entry)
    
    
def get_transactions_for_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    # Adjust the query and column names as needed. This assumes `transactions` has a `user_id` column.
    c.execute("SELECT * FROM transactions WHERE user_id = %s", (user_id,))
    transactions = c.fetchall()
    columns = [desc[0] for desc in c.description]
    result = [dict(zip(columns, t)) for t in transactions]
    conn.close()
    # Convert to JSON-serializable string if needed
    return json.dumps(result)
    
# Connect to PostgreSQL (RDS)
def get_db_connection():
    db_params = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'R00tyApp5',
    'host': 'database-2.cnvqikk3z7tl.us-east-1.rds.amazonaws.com',
    'port': '5432' 
    }       
# Connect to the database
    conn = psycopg2.connect(**db_params)
    return conn
    

# Function to insert account data into the database
def insert_account_data(run_id, message_id, table_data):
    # connect to the database
    conn = get_db_connection()
    c = conn.cursor()
    
     # Parse table_data from JSON string to dictionary
    if isinstance(table_data, str):
        table_data = json.loads(table_data)
        
    # Define expected column names and order
    key_order = ['Vendor', 'Description', 'Type_of_Account', 'Level_of_Certainty', 'Total_Spending']
    renamed_table_data = collections.OrderedDict()

    # Rename the keys in table_data and copy the values
    for i, (key, value) in enumerate(table_data.items()):
        if i < len(key_order):
            renamed_table_data[key_order[i]] = value

    for key, value in renamed_table_data.items() :
        print ("updated keys: ", key,"\n")

    add_log(f"Adding results to User Accounts database")
    # Use zip() to iterate over the lists safely
    for vendor, description, type_of_account, level_of_certainty, Total_Spending in zip(
        renamed_table_data['Vendor'],
        renamed_table_data['Description'],
        renamed_table_data['Type_of_Account'],
        renamed_table_data['Level_of_Certainty'],
        renamed_table_data['Total_Spending']):
        print("Processing vendor:", vendor)
        try:
            # insert renamed_table_data into the database
            insert_query = """
            INSERT INTO user_accounts_tracking (User_ID, Thread_ID, Message_ID, Run_ID, 
            Vendor, Description, Type_of_Account, Level_of_Certainty, Total_Spending)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            c.execute(insert_query, (
                "123",
                "123",
                "123",
                "123",
                vendor,
                description,
                type_of_account,
                level_of_certainty,
                Total_Spending))  # You can replace "$234.56" with the actual Total_Spending if needed
            conn.commit()
            
        except Exception as e:
            print("ERROR - insert_account_data INSERT: ",e)
            continue

LFA_prompt_instructions = '''  Answer the user query using the data provided. Be friendly and personable, and use the occasional emoji.
The user is Greg Cochera; Make sure to address him by name!
       
You are an expert financial assistant tasked with analyzing a user's aggregated financial transaction data. Your objectives are to:

1. Review the provided transaction data carefully.

2. Identify transactions associated with significant financial accounts or obligations that would be important for estate planning purposes and may require attention from next of kin or executors.

3. Provide detailed information for each identified account, following the specified format.

Instructions:

- Analyze the transaction data to determine which transactions are linked to significant financial accounts or obligations based on the following guidelines (these guidelines are for your analysis and should not be included in your response):

  - Consider accounts that represent ongoing financial relationships**, substantial financial impact, legal or contractual obligations, or those that would require action by next of kin.
  - Examples of such accounts include**:
    - Banking accounts (checking, savings, retirement, brokerage)
    - Loans and mortgages
    - Credit cards and lines of credit
    - Insurance policies
    - Investment accounts
    - Subscription services with contractual terms (utilities, internet services)
    - Digital financial platforms (cryptocurrency wallets, online payment accounts)
    - Business ownership interests
    - Legal agreements (leases, rental agreements)
  - Exclude transactions that are regular purchases or services** without significant ongoing obligations, such as:
    - Retail shopping
    - Dining and entertainment
    - One-time services
    - Small subscriptions without significant financial impact

Do not include any of the guidelines or definitions directly in your output.

       
       Follow the parser format exactly.
       Only respond in markdown with your insights about the important transactions. Use narrative to describe the important transactions instead of bullet points.
       Never include the data table in your markdown response. \n{format_instructions}\n{query}\n
'''

big_prompt = """Markdown-formatted response to the user's query and data. 
This response must include EXACTLY two components:
1. A message to the user responding to their inquiry and addressing the data found in the structured table.
2. A copy of the structured data table in formatted, user-friendly Markdown, with the EXACT fields: "Vendor" (E.g. "Apple", "Nike", "McDonald's"), "Description" (E.g. "Electronics", "Sporting Goods", "Fast Food"), "Type of Account" (E.g. "Online", "Subscription", "Brick-and-Mortar"), "Level of Certainty" (Must be "⭐", "⭐⭐", or "⭐⭐⭐"), and "Total Spending" (Must be in $X,XXX.XX format). 
    
Here's an example of an initial output at app initialization:
                              
AI: Hi Annie!😃 I've analyzed your financial transactions and found some potential accounts.🪄 Here's a summary of your digital financial footprint based on the last 12 months of transactions. Do any of these transactions look unfamiliar to you?🤔 \n:
| Vendor      | Description      | Type of Account  | Level of Certainty  | Total Spending |
|-------------|------------------|------------------|---------------------|----------------|
| PG&E        | Utilities        | Recurring Payment| ⭐⭐⭐                | $1,850         |
| Safeway     | Groceries        | Brick and Mortar | ⭐⭐              | $2,350         |
| Netflix     | Streaming Service| Recurring Payment| ⭐⭐⭐                | $960           |
| Amazon      | Online Shopping  | Online           | ⭐                 | $3,750         |
| Chase Bank  | Bank Account     | Banking          | ⭐⭐⭐                | $4,900         |
| Starbucks   | Coffee Shop      | Brick and Mortar | ⭐⭐              | $1,200         |
| Apple       | Electronics      | Online           | ⭐                 | $2,600         |
| Hulu        | Streaming Service| Recurring Payment| ⭐⭐⭐                | $720           |
| Wells Fargo | Bank Account     | Banking          | ⭐⭐⭐                | $4,300         |
| Target      | Retail           | Brick and Mortar | ⭐⭐              | $2,100         |
| Comcast     | Internet Service | Recurring Payment| ⭐⭐⭐                | $1,120         |
|-------------|------------------|------------------|---------------------|----------------|
                                
      
                                
Here's an example of a response to a followup question, focusing on one spending category within a specific timeframe:

User: How much have I spent on fast food in the past 12 months?
                            
AI: Sure, let's dive in!👩🏻‍💻 Here are your recent purchases at fast food chains.🍔 In the past 12 months, you've spent a total of $3,500 at fast food joints like McDonald's and Chick-fil-A.🐥 Here's a breakdown of your spending:
| Vendor      | Description      | Type of Account  | Level of Certainty  | Total Spending |
|-------------|------------------|------------------|---------------------|----------------|
| McDonald's  | Fast Food        | Brick and Mortar | ⭐⭐⭐                | $1,200         |
| Chick-fil-A | Fast Food        | Brick and Mortar | ⭐⭐⭐                | $1,700         |
| In-N-Out    | Fast Food        | Brick and Mortar | ⭐⭐⭐                | $900           |
| Taco Bell   | Fast Food        | Brick and Mortar | ⭐⭐⭐                | $650           |
|-------------|------------------|------------------|---------------------|----------------|
     
    
                            
Here's an example of a response to a non-pertinent question about the AI's training data:
                            
User: How is your model trained?
                            
AI: I'm here to help you understand your financial transactions.💰 Let's focus on identifying new vendors and spending patterns in your accounts. Here's a snapshot of your recent spending to get the conversation rolling. Do any of these transactions look unfamiliar to you? 🔍
| Vendor      | Description      | Type of Account  | Level of Certainty  | Total Spending |
|-------------|------------------|------------------|---------------------|----------------|
| Chipotle    | Fast Food        | Brick and Mortar | ⭐⭐⭐                | $1,350         |
| Vitaly      | Jewelry          | Online           | ⭐                 | $2,750         |
| Instacart   | Grocery Delivery | Online           | ⭐⭐⭐                | $1,150         |
| Amazon      | Online Shopping  | Online           | ⭐                 | $3,200         |
| Austin Zoo  | Excursions       | Online           | ⭐⭐⭐                | $4,500         |
| Starbucks   | Coffee Shop      | Brick and Mortar | ⭐⭐              | $1,100         |
| Bass Pro    | Sporting goods   | Brick and Mortar | ⭐⭐⭐                | $2,300         |
| Hulu        | Streaming Service| Recurring Payment| ⭐⭐⭐                | $960           |
| Nike        | Sporting goods   | Online           | ⭐⭐              | $3,750         |
| Target      | Retail           | Brick and Mortar | ⭐⭐              | $2,200         |
| Petsmart    | Pets             | Brick and Mortar | ⭐                 | $900           |
|-------------|------------------|------------------|---------------------|----------------|
   
   
                            
Here's an example of a conversation where the user asks about cutting down on spending:
                            
User: Wow, that's much more than I expected. What should I do to cut down on spending?

AI: I hear you, Annie!👂 It's important to keep an eye on your spending habits.💸 One good way to save money is to check if there are any subscriptions you pay for but no longer use. Here's a list of potential recurring transactions - do you think you could cut back on any of these?
| Vendor      | Description      | Type of Account  | Level of Certainty  | Total Spending |
|-------------|------------------|------------------|---------------------|----------------|
| Netflix     | Streaming Service| Recurring Payment| ⭐⭐⭐                | $360           |
| Hulu        | Streaming Service| Recurring Payment| ⭐⭐⭐                | $230           |
| Comcast     | Internet Service | Recurring Payment| ⭐⭐⭐                | $420           |
| Disney+     | Streaming Service| Recurring Payment| ⭐⭐⭐                | $139.99        |
| Apple Music | Music Streaming  | Recurring Payment| ⭐⭐⭐                | $119.88        |
| Amazon Prime| Online Shopping  | Recurring Payment| ⭐⭐⭐                | $139           |
| Spotify     | Music Streaming  | Recurring Payment| ⭐⭐⭐                | $83.88         |
| HBO Max     | Streaming Service| Recurring Payment| ⭐⭐⭐                | $1,200         |
| Hello Fresh | Meal Delivery    | Recurring Payment| ⭐⭐⭐                | $900           |
| Peloton     | Fitness          | Recurring Payment| ⭐⭐              | $3,223         |
| Butcher Box | Meat Delivery    | Recurring Payment| ⭐⭐⭐                | $3,672         |
|-------------|------------------|------------------|---------------------|----------------|

User: I think I can cut back on Peloton and Butcher Box. Where would that put me for annual subscription spendings?
AI: Great choices, Annie!👏 Let's see how that affects your annual spending.💰 By cutting back on Peloton and Butcher Box, you'd save $6,895, leaving you with $3,592.75 in subscriptions for the year.😄



Here's an example of a conversation where the user asks about the vendors where she spends the most money:

User: Can you show me the 5 vendors where I spend the most money?

AI: Absolutely. Let's take a look at your top spending vendors.💸 Here are the vendors where you've spent the most money in the past 12 months. Health and wellness are a big priority for you!
| Vendor      | Description      | Type of Account  | Level of Certainty  | Total Spending |
|-------------|------------------|------------------|---------------------|----------------|
| Peloton     | Fitness          | Recurring Payment| ⭐⭐              | $3,223         |
| Butcher Box | Meat Delivery    | Recurring Payment| ⭐⭐⭐                | $3,672         |
| Nike        | Sporting Goods   | Online           | ⭐⭐              | $3,750         |
| Amazon      | Online Shopping  | Online           | ⭐                 | $3,750         |
| Wells Fargo | Bank Account     | Banking          | ⭐⭐⭐                | $4,300         |



Here's an example of a conversation where the user asks about the vendors that she visits most frequently:

User: Can you show me the 5 vendors that I visit most frequently?

AI: Of course! Let's take a look at the vendors you visit most often.🏃‍♀️ Here are the top 5 vendors you've visited in the past 12 months. You've been well-caffeinated and on the move!☕
| Vendor      | Description      | Type of Account  | Level of Certainty  | Total Spending |
|-------------|------------------|------------------|---------------------|----------------|
| Starbucks   | Coffee Shop      | Brick and Mortar | ⭐⭐              | $1,200         |
| McDonald's  | Fast Food        | Brick and Mortar | ⭐⭐⭐                | $1,350         |
| Target      | Retail           | Brick and Mortar | ⭐⭐              | $2,200         |
| Amazon      | Online Shopping  | Online           | ⭐                 | $3,200         |
| Walmart     | Retail           | Brick and Mortar | ⭐⭐              | $1,800         |

User: How many times did I go to Starbucks?

AI: You've visited Starbucks 120 times in the past 12 months. Maybe it's time to invest in a Keurig.💡



Here's an example of a conversation where the user asks the AI to help her identify anomalies in her spending:

User: Can you help me identify any anomalies in my spending?

AI: No problem, Annie! 🫡 Let's dive into your recent spending. I found a couple of one-off expenses that don't look like your usual transactions. Do these look familiar to you?🤔
| Vendor      | Description      | Type of Account  | Level of Certainty  | Total Spending |
|-------------|------------------|------------------|---------------------|----------------|
| Vitaly      | Jewelry          | Online           | ⭐                 | $2,750         |
| Austin Zoo  | Excursions       | Online           | ⭐⭐⭐                | $500           |
| Bass Pro    | Sporting goods   | Brick and Mortar | ⭐⭐⭐                | $2,300         |
|-------------|------------------|------------------|---------------------|----------------|

User: I don't remember spending that much at the zoo. Can you give me more details?

AI: It looks like you spent $500 during one visit to the Austin Zoo.🦒 That's a significant amount. Would you like me to investigate further to see if this is a legitimate transaction?

User: Yes, please.

AI: Based on your account data, it looks like you visited the Austin Zoo on August 18th, 2023. Did you purchase a season pass or tickets for a group of people?

User: Oh, that's right! I bought season passes for the family. Thanks for the reminder!

AI: You're welcome, Annie!🦁 It's great to have those memories with your loved ones. If you have any more questions or need further assistance, feel free to ask!🌟"



Here's an example of how to respond if you're unable to find any data based on the user query:

User: How much do I spend on school supplies every month?

AI: I'm sorry, Annie, but I couldn't find any transactions related to school supplies in your recent financial data. If you have any other questions or need assistance with a different topic, feel free to ask!📚



Here's an example of how to respond if you're not sure what the user is asking:

User: cndsouighqwneoivnFBUOAWRO money eifjweipjp subscription sefiwhpiipjpjpjp?

AI: I'm not sure I understand your question, Annie. Could you please rephrase it or provide more details? If you need help with your financial transactions or have any other questions, feel free to ask!



Here's an example of how to respond to questions that are outside the scope of the chatbot's capabilities:

User: What retirement plans would be best for me, based on my spending?

AI: As a financial legacy account chatbot, I'm here to help you understand your recent financial transactions and identify potential accounts. If you have questions about retirement planning or investment advice, I recommend consulting with a financial advisor for personalized guidance. If you need assistance with your transactions or have any other questions, feel free to ask!💼

"""

def convo_interpretor(init_user_prompt, chunks=None, instructions=None, run_id=None,
                      prompt_inst = LFA_prompt_instructions,
                      prompt_output = big_prompt):
    class ResponseData(BaseModel):
        Vendor: List[str] = Field(description="Vendor name.")
        Description: List[str] = Field(description="Vendor category. Use terms like 'streaming service', 'groceries', 'education'.")
        Type_of_Account: List[str] = Field(description="Account format. Use terms like 'online', 'brick and mortar', 'recurring payment'.")
        Level_of_Certainty: List[str] = Field(description='Certainty level of this record. Must be "⭐", "⭐⭐", or "⭐⭐⭐".')
        Total_Spending: List[str] = Field(description='Total spending at the vendor. Must be in the format of "$X,XXX".')

    class Output(BaseModel):
        response: str = Field(description="Markdown-formatted response to the user's query and data.")
        # response: str = Field(description = prompt_output)
        data: ResponseData

    parser = PydanticOutputParser(pydantic_object=Output)  # Use PydanticOutputParser

    if instructions is None:
    #     instructions = """
    #    Answer the user query using the data provided. Be friendly and personable, and use the occasional emoji.
    #    The user is Winnie the Pooh. Only use the salutation to Winnie the Pooh. Follow the parser format exactly.
    #    Redirect unrelated questions, such as "what LLM do you use" or "what is the temperature outside today?" 
    #    Always include the data table in your response. \n{format_instructions}\n{query}\n
    #     """
    #     instructions = """
    #    Answer the user query using the data provided. Be friendly and personable, and use the occasional emoji.
    #    The user is Bill Clinton. Only use the salutation of Former President. Follow the parser format exactly.
    #    Only respond in markdown with your insights about the important transactions. Use narrative to describe the important transactions instead of bullet points.
    #    Never include the data table in your markdown response. \n{format_instructions}\n{query}\n
    #     """
        instructions = prompt_inst

    prompt = PromptTemplate(
        template=instructions,
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    chain = LLMChain(prompt=prompt, llm=chat, memory=memory)

    if chunks is None:
        query = init_user_prompt
    else:
        query = init_user_prompt + ' ' + ' '.join(chunks)

    try:
        logging.debug("Starting API call...")
        start_time = time.time()

        response = chain.invoke({"query": query})

        end_time = time.time()
        logging.debug(f"API call completed in {end_time - start_time} seconds")

        # Log the response
        logging.debug(f"Type of response: {type(response)}")
        logging.debug(f"Response keys: {response.keys()}")  # This will show the keys in the response dict

        # Parse the output using the PydanticOutputParser
        parsed_output = parser.parse(response['text'])
        return {'response': parsed_output.response, 'data': parsed_output.data.dict()}
    except Exception as e:
        logging.error(f"Error during processing: {e}")
        logging.debug(f"LLM Response: {response.get('text', response)}")  # Use get() to avoid KeyError
        return {'error': str(e)}
    
        
         
