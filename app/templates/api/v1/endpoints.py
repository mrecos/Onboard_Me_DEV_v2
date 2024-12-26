# app/templates/api/v1/endpoints.py

import json                   # for json
from json import dumps        # for json dumps
from json import loads        # for json loads
import time 
from flask import Blueprint, jsonify, request
from app.core import (
    log_messages,
    llm_outputs,
    add_log,
    get_db_connection,
    convo_interpretor,
    get_transactions_for_user,
    insert_account_data
)



api_v1 = Blueprint('api_v1', __name__)

# @api_v1.route('/initiate', methods=['GET'])
# def init_convo():
#     # Your existing initiate endpoint code
#     user_id = request.args.get('user_id', None)
#     if not user_id:
#         return jsonify({"error": "User ID is required"}), 400
    
#     # Rest of your existing code
#     pass


@api_v1.route('/initiate', methods=['GET'])
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

@api_v1.route('/logs')
def get_logs():
    # Return the entire log_messages list as JSON.
    # For a real app, you might do some limit or offset.
    return jsonify(log_messages)

@api_v1.route('/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()

    user_list = [{"id": u[0], "name": u[1], "age": u[2]} for u in users]
    return jsonify({"users": user_list})

@api_v1.route('/llm_outputs')
def get_llm_outputs():
    """Return the stored LLM outputs (Markdown) as JSON."""
    return jsonify(llm_outputs)
    