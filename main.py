from flask import Flask, request, jsonify, render_template_string
import mysql.connector
import google.generativeai as genai
import os
from datetime import datetime
import json
import re
from dotenv import load_dotenv
from decimal import Decimal
import markdown


# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
MYSQL_CONFIG = {
    'host': '217.21.80.10',
    'user': 'u196817721_nagpurUser3',
    'password': 'Nagpur#FORMS25',
    'database': 'u196817721_nagpurAllForms'
}

#कृषि विभागाचा मंजूर नियतव्यय किती आहे?

# Configure Gemini AI
genai.configure(api_key='AIzaSyD6OVR_dU_RIv2U-5Wy7dulQEX4M_h7fzE')
model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

# Database schema information
SCHEMA_INFO = """
Table1: funds_info
- `id` int(11) NOT NULL,
- `year` varchar(10) NOT NULL,
- `head` varchar(255) NOT NULL,
- `sub_head` varchar(255) NOT NULL,
- `fund` varchar(255) NOT NULL,
- `department` varchar(255) NOT NULL,
- `scheme` varchar(255) NOT NULL,
- `sanction_amount` decimal(15,2) NOT NULL,
- `received_amount` decimal(15,2) NOT NULL,
- `utilised_amount` decimal(15,2) NOT NULL,
- `created_at` timestamp NULL DEFAULT current_timestamp(),
- `user_id` varchar(255) NOT NULL
"""

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        return connection
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

def generate_sql_query(natural_query):
    """Convert natural language query to SQL using Gemini AI"""
    prompt = f"""
    You are a SQL expert. Convert the following natural language query to a MySQL SELECT statement.
    
    {SCHEMA_INFO}
    
    IMPORTANT:
    1. Find the relevant match data from the schema information provided. 
        (e.g. 1. In table department 'कृषि विभाग' is stored as 'कृषी विभाग'. So you need to find the relevant match data from the schema information provided
        2. In table department 'agriculture department' is stored as 'कृषी विभाग'. So you need to find the relevant match data from the schema information provided
        )

    

    Rules:
    1. Only generate SELECT statements for data retrieval
    2. Use proper MySQL syntax
    3. Return only the SQL query without any explanation
    4. If the query involves counting, use COUNT() function
    5. If the query involves aggregation, use appropriate functions like SUM(), AVG(), etc.
    6. Always use proper WHERE clauses when filtering is needed
    7. Use LIMIT when appropriate for top/bottom queries
    8. Do not include any comments or explanations in the SQL query
    9. Ensure the query is safe and does not expose sensitive data.
    10. If the query related to manupulating data, return an error message saying "This query is not supported. Please ask a question about retrieving data only."
    
    Natural Language Query: {natural_query}
    
    SQL Query:
    """
    
    try:
        response = model.generate_content(prompt)
        sql_query = response.text.strip()
        
        # Clean the SQL query (remove any markdown formatting)
        sql_query = re.sub(r'```sql\n|```\n|```', '', sql_query)
        sql_query = sql_query.strip()
        
        return sql_query
    except Exception as e:
        print(f"Error generating SQL: {e}")
        return None

def execute_sql_query(sql_query):
    """Execute SQL query and return results"""
    connection = get_db_connection()
    if not connection:
        return None, "Database connection failed"
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql_query)
        results = cursor.fetchall()
        
         # Convert datetime and Decimal objects to serializable types
        for row in results:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, Decimal):
                    row[key] = float(value)  # Convert Decimal to float
        
        cursor.close()
        connection.close()
        return results, None
    except mysql.connector.Error as err:
        connection.close()
        return None, f"SQL execution error: {err}"

def generate_natural_response(natural_query, sql_query, results):
    """Generate natural language response using Gemini AI"""
    prompt = f"""
    You are a helpful assistant that explains database query results in natural language.
    
    Original Question: {natural_query}
    SQL Query Used: {sql_query}
    Query Results: {json.dumps(results, indent=2)}
    
    Please provide a natural, conversational response that answers the user's question based on the results.
    
    IMPORTANT RULES:
    1. NEVER mention database terms like "database", "table", "column", "SQL", "query", "schema", "users table", etc.
    2. NEVER describe technical database structure or mention table/column names
    3. Focus ONLY on the actual data and answering the user's question
    4. Be conversational and friendly
    5. Mention specific numbers, names, or details from the data when relevant
    6. If there are no results, say so naturally without technical terms
    7. Speak as if you're directly aware of the users/people, not accessing a database
    8. Use terms like "users", "people", "individuals" naturally, not "records" or "rows"
    9. Avoid the personal details of users such as emails, phone numbers, etc.
    
    Examples of good responses:
    - "There are 150 users." (NOT "There are 150 users in the users table")
    - "I found 25 people from Mumbai." (NOT "There are 25 records with city=Mumbai")
    - "The average age is 28 years." (NOT "The average age column value is 28")
    Response:
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I found the data, but I'm having trouble explaining it right now."

@app.route('/')
def index():
    """Main page with query interface"""

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, shrink-to-fit=no">
        <title>Ask AI</title>
        
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .query-box { margin: 20px 0; }
            input[type="text"] { width: 100%; padding: 15px; font-size: 16px; border: 2px solid #ddd; border-radius: 5px; }
            button { background: #007bff; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin-top: 10px; }
            button:hover { background: #0056b3; }
            .response { margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #007bff; }
            .error { background: #f8d7da; border-left: 4px solid #dc3545; color: #721c24; }
            .examples { margin: 20px 0; }
            .example { background: #e9ecef; padding: 10px; margin: 5px 0; border-radius: 3px; cursor: pointer; }
            .example:hover { background: #dee2e6; }
            .loading { display: none; color: #007bff; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Ask AI</h1>
            <p>Ask natural language questions about your users database!</p>
            
            <div class="query-box">
                <input type="text" id="queryInput" placeholder="Ask me anything about your users... (e.g., 'How many users are there?')" />
                <button onclick="submitQuery()">Ask AI</button>
                <div class="loading" id="loading">🤔 Thinking...</div>
            </div>

            <div id="response"></div>   
            
            <div class="examples">
                <h3>Try these examples:</h3>
                <div class="example" onclick="setQuery('Give me total number of users')">Give me total number of users</div>
                <div class="example" onclick="setQuery('How many male users are there?')">How many male users are there?</div>
                <div class="example" onclick="setQuery('Show me users from Mumbai')">Show me users from Mumbai</div>
                <div class="example" onclick="setQuery('Show me the youngest user')">Show me the youngest user</div>
            </div>
            
            
        </div>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

        <script>
            function setQuery(query) {
                document.getElementById('queryInput').value = query;
            }
            
            function submitQuery() {
                const query = document.getElementById('queryInput').value;
                if (!query.trim()) {
                    alert('Please enter a question!');
                    return;
                }
                
                document.getElementById('loading').style.display = 'block';
                document.getElementById('response').innerHTML = '';
                
                fetch('/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({query: query})
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('loading').style.display = 'none';
                    if (data.success) {
                        const html = marked.parse(data.response); // 🔄 Markdown to HTML
                        document.getElementById('response').innerHTML = 
                            `<div class="response">
                                <strong>Response:</strong> 
                                ${html}
                            </div>`;
                    } else {
                        document.getElementById('response').innerHTML = 
                            `<div class="response error">
                                <strong>Error:</strong> ${data.error}
                            </div>`;
                    }
                })
                .catch(error => {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('response').innerHTML = 
                        `<div class="response error">
                            <strong>Error:</strong> Something went wrong. Please try again.
                        </div>`;
                });
            }
            
            // Allow Enter key to submit
            document.getElementById('queryInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    submitQuery();
                }
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

@app.route('/query', methods=['POST'])
def process_query():
    """Process natural language query and return response"""
    try:
        data = request.get_json()
        natural_query = data.get('query', '').strip()
        
        if not natural_query:
            return jsonify({
                'success': False,
                'error': 'Please provide a query'
            })
        
        # Step 1: Generate SQL query
        sql_query = generate_sql_query(natural_query)
        print(f"Generated SQL Query: {sql_query}")
        if not sql_query:
            return jsonify({
                'success': False,
                'error': 'Failed to generate SQL query'
            })
        
        # Step 2: Execute SQL query
        results, error = execute_sql_query(sql_query)
        print(f"SQL Query Results: {results}")
        if error:
            return jsonify({
                'success': False,
                'error': error
            })
        
        # Step 3: Generate natural language response
        natural_response = generate_natural_response(natural_query, sql_query, results)
        print(f"Natural Language Response: {natural_response}")
        return jsonify({
            'success': True,
            'response': natural_response,
            'raw_results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # Test database connection on startup
    conn = get_db_connection()
    if conn:
        print("✅ Database connection successful")
        conn.close()
    else:
        print("❌ Database connection failed")
    
    print("🚀 Starting Flask AI SQL Query application...")
    print("📝 Remember to:")
    print("   1. Update MYSQL_CONFIG with your database credentials")
    print("   2. Set your Gemini API key")
    print("   3. Ensure your MySQL server is running")
    
    app.run(debug=True, host='0.0.0.0', port=5000)