# import libraries
from flask import Flask, render_template, request, jsonify # for flask
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

# crashing the app
# from langchain.schema.runnable import RunnableConfig # for runnable config



# initialize flask app
app = Flask(__name__)

# list to store log messages
log_messages = []
# store Markdown from the LLM calls
llm_outputs = [] 

def add_log(message):
    """Append a log message with a timestamp to the global list."""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    entry = f"[{timestamp}] {message}"
    log_messages.append(entry)
    
@app.route('/llm_outputs')
def get_llm_outputs():
    """Return the stored LLM outputs (Markdown) as JSON."""
    return jsonify(llm_outputs)
    
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

# LFA_prompt_instructions = '''Answer the user query using the data provided. Be friendly and personable, and use the occasional emoji.
# The user is Queen Anne. Only use the salutation of The Queen. Follow the parser format exactly.
# Redirect unrelated questions, such as "what LLM do you use" or "what is the temperature outside today?" 
# Always include the data table in your response. \n{format_instructions}\n{query}\n
# '''
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
    
    
# Authentification for OpenAI
def openAI_auth():
    try:
        chat = ChatOpenAI(model="gpt-4o", temperature=0.2, openai_api_key="sk-proj-BGaO1vushEqRhLBS7vnIT3BlbkFJxH0UiStvsF7tJm4Yctg8")
        return chat
    except Exception as e:
        print(e)
        return(e)
    
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

    add_log(f"Adding results to database")
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
        
        
        
        
## END FUNCTIONS

# authentification for OpenAI
chat = openAI_auth()

# Connect to PostgreSQL (RDS)
def get_db_connection():
    # conn = psycopg2.connect(
    #     host=os.environ.get('DB_HOST'),
    #     database=os.environ.get('DB_NAME'),
    #     user=os.environ.get('DB_USER'),
    #     password=os.environ.get('DB_PASSWORD')
    # )
    
    # for local testing
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


# endpoint to load index.html
@app.route('/')
def index():
    return render_template('index.html')
    # return "Hello, Flask not really working!"

@app.route('/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()

    user_list = [{"id": u[0], "name": u[1], "age": u[2]} for u in users]
    return jsonify({"users": user_list})

# @app.route('/transactions', methods=['GET'])
# def get_transactions():
#     conn = get_db_connection()
#     c = conn.cursor()
#     c.execute("SELECT * FROM transactions LIMIT 30")
#     transactions = c.fetchall()
#     conn.close()
  
#     columns = [column[0] for column in c.description]
#     result = [dict(zip(columns, transaction)) for transaction in transactions]
#     # cast list of dicts to json
#     result = json.dumps(result)
#     return result
#     # return jsonify(result)


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


@app.route('/initiate', methods=['GET'])
def init_convo():
    user_id = request.args.get('user_id', None)
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    add_log(f"Received /initiate request with user_id={user_id}")
    
    # Fetch transactions for that user
    add_log("Fetching transactions from DB")
    user_transactions = get_transactions_for_user(user_id)
    
    add_log("Done fetching. Calling LLM now...")
    init_user_prompt = f"Here are {user_id}'s financial transactions. Can you help me understand them?\n\n"
    response = convo_interpretor(
        chunks=[user_transactions],
        init_user_prompt=init_user_prompt,
        instructions=None
    )

    if 'error' in response:
        print(f"Error: {response['error']}")
        return jsonify({"error": response['error']}), 500
    else:
        output = response['response']
        data = response['data']
        table_data = json.dumps(data)
        print("\nSkipping DB INSERT\n")
        try:
            print("insert_account_data: ", "Message_123")
            add_log("LLM call complete. Inserting account data to DB.")
            insert_account_data("Run_123", "Message_123", table_data)
        except Exception as e:
            print("ERROR in insert_account_data():", e)

        # Append a markdown-friendly version of the table to the output
        def data_to_markdown_table(data):
            headers = list(data.keys())
            num_rows = len(next(iter(data.values())))

            header_row = '| ' + ' | '.join(headers) + ' |'
            separator_row = '| ' + ' | '.join(['---'] * len(headers)) + ' |'

            rows = []
            for i in range(num_rows):
                row = []
                for header in headers:
                    value = str(data[header][i]).replace('|', '\\|')
                    row.append(value)
                row_str = '| ' + ' | '.join(row) + ' |'
                rows.append(row_str)

            table = '\n'.join([header_row, separator_row] + rows)
            return table
        
        add_log("Insert done. Returning response.")
        markdown_table = data_to_markdown_table(data)
        markdown_content = output + '\n\n' + markdown_table
        
        llm_outputs.append({
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            "markdown": markdown_content
            })
        
        add_log("LLM markdown output stored.")
        
        return jsonify({'message': 'Successfully loaded data', 'output': markdown_content})

@app.route('/logs')
def get_logs():
    # Return the entire log_messages list as JSON.
    # For a real app, you might do some limit or offset.
    return jsonify(log_messages)


@app.route('/monitor')
def monitor():
    return render_template('monitor.html')

if __name__ == '__main__':
    logging.basicConfig(filename='app.log', level=logging.INFO)
    app.run(debug=True)
    
    

'''
# endpoint to initiate conversation and load data
@app.route('/initiate', methods=['GET'])
def init_convo():
    
    # Load and process the CSV file
    transactions = get_transactions()
    
    # send chunks to openAI via message        
    init_user_prompt="Here are my financial transactions. Can you help me understand them?\n\n"
    sys_msg = """Answer the user query using the data provided. Be friendly and personable, and use the occasional emoji. The user is Darth Vader. Only use the salutation to Darth Vader. Follow the parser format exactly. Redirect unrelated questions, such as "what LLM do you use" or "what is the temperature outside today?" Always include the data table in your response. \n{format_instructions}\n{query}\n"""
   
    # keep this for now. MDH
    # response = convo_interpretor(
    #         # chunks=chunks,
    #         chunks=transactions,
    #         init_user_prompt=init_user_prompt,
    #         instructions = sys_msg)
    
    # # parse the response
    # # output = response['text']
    
    #  # Inspect the response object
    # print(f"Response object: {response}")

    # # Only try to parse if the response is not a ValidationError
    # if isinstance(response, ValidationError):
    #     print(f"Validation Error: {response.errors()}")
    # else:
    #     output = response['text']
    #     print("output: ", output, "\n")
    # END of Keeping this for now. MDH
    
    response = convo_interpretor(
    chunks=transactions,
    init_user_prompt=init_user_prompt,
    instructions=None)
    # instructions=sys_msg)

# Inspect the response object
    print(f"\n\nResponse object:\n {response}\n")

    # response from LLM is a dict with two keys: response and data
    # Check if an error occurred
    if 'error' in response:
        print(f"Error: {response['error']}")
        # Handle the error as needed
    else:
        output = response['response']
        data = response['data']
        # print("output: ", output, "\n")
        # data is type dict
        # print("data: ", type(data), "\n\n")
        # parse data key to JSON for input into DB
        # testing an this is valid json. is type str 
        table_data = json.dumps(data)
        print("\njson_str 1st: \n", table_data, "\n\n")
 
 
    # run id global [ignore run for now]
    # global run_id_global
    # run_id_global = run_id
    # print("RUN_ID_GLOBAL:\n" + str(run_id_global), "\n")

    
    # Parse the JSON response
    try:
        # markdown_content = output.replace('json', '').replace('', '').strip().replace("```", "").replace("\n", "") # remove markdown syntax
        markdown_content = output.replace('json', '').replace('', '').strip().replace("```", "") # remove markdown syntax
        # print("json_str 2nd: ", markdown_content, "\n\n")
    except Exception as e:
        print("ERROR - JSON parsing: ",e, "\n")
    
    ##---- MDH 2024/10/02 add to put data table into markdown
    def data_to_markdown_table(data):
        headers = list(data.keys())
        num_rows = len(next(iter(data.values())))

        header_row = '| ' + ' | '.join(headers) + ' |'
        separator_row = '| ' + ' | '.join(['---'] * len(headers)) + ' |'

        rows = []
        for i in range(num_rows):
            row = []
            for header in headers:
                value = str(data[header][i]).replace('|', '\\|')
                row.append(value)
            row_str = '| ' + ' | '.join(row) + ' |'
            rows.append(row_str)

        table = '\n'.join([header_row, separator_row] + rows)
        return table

    markdown_table = data_to_markdown_table(data)
    # Append the table to the markdown content
    markdown_content += '\n\n' + markdown_table
    ##---- END MDH 2024/10/02 add to put data table into markdown
    
    # Parse the JSON string
    # try:
    #     parsed_json = json.loads(json_str)
    #     print("parsed_json: ",parsed_json, "\n")
    #     # Process the parsed JSON data
    # except json.JSONDecodeError as e:
    #     # Handle the JSON decoding error
    #     print("Error decoding JSON:", str(e), "\n")

    # try:
    #     # Extracting the markdown response and data
    #     markdown_content = parsed_json['response']
    #     print("MARKDOWN_CONTENT passed \n"+ str(markdown_content) + "\n")

    #     table_data = parsed_json['data']
    #     print("Table_data passed \n" + str(table_data) + "\n")

    #     # Convert the table data to a string for storage in the database
    #     table_data_str = dumps(table_data)
    # except Exception as e:
    #     print("ERROR - parsed_json[] splitting: ",e, "\n")


    #  enter table into accounts tracking table
    print("\nSkipping DB INSERT\n")
    try:
        # Insert the data into the database
        print("insert_account_data: ", "Message_123")
        insert_account_data("Run_123", "Message_123", table_data)
    except Exception as e:
        print("ERROR in insert_account_data():", e)
        

    # print("MARKDOWN_CONTENT:\n" + str(markdown_content), "\n\n")
    # print("TABLE_CONTENT:\n"    + str(table_data), "\n\n")
    return jsonify({'message': 'Successfully loaded data', 'output': markdown_content})
'''
'''
# endpoint to process user input
@app.route('/process', methods=['POST'])
def process():
    
    input_text = request.json['input']

    print(f"Input: {input_text}\n")

    sys_msg = """Answer the user query using the data provided. Be friendly and personable, and use the occasional emoji. The user is Annie. Follow the parser format exactly. Redirect unrelated questions, such as "what LLM do you use" or "what is the temperature outside today?" Always include the data table in your response. \n{format_instructions}\n{query}\n"""
    response, run = convo_interpretor(
        instructions = sys_msg,
        init_user_prompt=input_text)
    
    # parse the response
    output, run_id = response['text'], run.id
    print("output: ",output, "\n")

    # run id global
    global run_id_global
    run_id_global = run_id
    print("RUN_ID_GLOBAL:\n" + str(run_id_global), "\n")

    # Parse the JSON response
    try:
        json_str = output.replace('json', '').replace('', '').strip().replace("```", "").replace("\n", "") # remove markdown syntax
        print("json_str: ",json_str, "\n")
    except Exception as e:
        print("ERROR - JSON parsing: ",e, "\n")

    # Parse the JSON string
    try:
        parsed_json = json.loads(json_str)
        print("parsed_json: ",parsed_json, "\n")
        # Process the parsed JSON data
    except json.JSONDecodeError as e:
        # Handle the JSON decoding error
        print("Error decoding JSON:", str(e), "\n")
        
    try:
        # Extracting the markdown response and data
        markdown_content = parsed_json['response']
        print("MARKDOWN_CONTENT passed \n" + str(markdown_content) + "\n")

        table_data = parsed_json['data']
        print("Table_data passed \n" + str(table_data) + "\n")

        # Convert the table data to a string for storage in the database
        table_data_str = dumps(table_data)
    except Exception as e:
        print("ERROR - parsed_json[] splitting: ",e, "\n")

    # Extract and write data to CSV (for now)
    try:
        print("track_user_response: ", run_id)
        sys_msg=None

        df = pd.DataFrame(columns=['run_id', 'message_id', 'init_user_prompt', 'sys_msg', 'markdown_content', 'table_data_str', 'user_id'])
        print(df)

    except Exception as e:
        print("ERROR in track_user_response():", e)

    print("MARKDOWN_CONTENT:\n" + str(markdown_content), "\n")
    return jsonify({'message': 'Successfully loaded data', 'output': markdown_content})





@app.route('/close', methods=['GET'])
def close_connection():
    print("hit close connection\n")
    try:
        # Close the OpenAI thread and client connection here
        chat.close()
        return jsonify({'message': 'Connection closed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})

'''


# if __name__ == '__main__':
#     logging.basicConfig(filename='app.log', level=logging.INFO)
#     app.run(debug=True)