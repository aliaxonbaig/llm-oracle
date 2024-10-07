# Credits for Original script with streamlit and hugginface 
# https://github.com/VRAJ-07/SQL-Chatbot-Using-LLM

import logging
import warnings
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy.engine import create_engine
from langchain.llms.base import LLM
from typing import Optional, List
import spacy
import ollama
from sqlalchemy import exc

warnings.filterwarnings("ignore", category=exc.SAWarning)
# Set up logging
#logging.basicConfig(level=logging.DEBUG)

username = 'hr'
password = 'hr'
host = 'localhost'
port = '1521'  # Default Oracle port
service_name = 'FREE'



# Create the DSN (Data Source Name)
#dsn = f"(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={host})(PORT={port}))(CONNECT_DATA=(SERVICE_NAME={service_name})))"

# Create the SQLAlchemy engine
engine = create_engine(f"oracle+cx_oracle://{username}:{password}@{service_name}")



# Custom Ollama LLM class that uses the ollama library
class OllamaLLM(LLM):
    model_name: str = "llama3.2:3b"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        #logging.debug(f"LLM Prompt: {prompt}")
        response = ollama.chat(model=self.model_name, messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        #logging.debug(f"LLM Response: {response}")
        return response['message']['content']

    @property
    def _identifying_params(self):
        return {"model_name": self.model_name}

    @property
    def _llm_type(self) -> str:
        return "ollama"

# Initialize the custom Ollama LLM
llm = OllamaLLM()

# Create SQLDatabase instance
db = SQLDatabase(engine)

# Load Spacy model
nlp = spacy.load("en_core_web_md")

def get_sql_chain(db):
    template = """
    You are an expert oracle database data analyst at a company. You are interacting with a user who is asking you questions about the our employees.

    Here is the schema of the hr employees table

 Name                                      Null?    Type
 ----------------------------------------- -------- ----------------------------
 EMPLOYEE_ID                               NOT NULL NUMBER(6)
 FIRST_NAME                                         VARCHAR2(20)
 LAST_NAME                                 NOT NULL VARCHAR2(25)
 EMAIL                                     NOT NULL VARCHAR2(25)
 PHONE_NUMBER                                       VARCHAR2(20)
 HIRE_DATE                                 NOT NULL DATE
 JOB_ID                                    NOT NULL VARCHAR2(10)
 SALARY                                             NUMBER(8,2)
 COMMISSION_PCT                                     NUMBER(2,2)
 MANAGER_ID                                         NUMBER(6)
 DEPARTMENT_ID                                      NUMBER(4)


    Write only the SQL query and nothing else.

    Do not wrap the SQL query in any other text, not even backticks.

    For example:

    Question: How many users?
    SQL Query: SELECT count(*) from employees


    Question: list all users with names starting with A
    SQL Query: SELECT FIRST_NAME, LAST_NAME FROM EMPLOYEES  WHERE FIRST_NAME LIKE 'A%%' ORDER BY FIRST_NAME ASC

    ** Notice there is not semicolun at the end of the statement **


    .......


Conversation History:
{chat_history}

Question: {question}
SQL Query:
"""
    prompt = ChatPromptTemplate.from_template(template)

    def get_schema(_):
        schema = db.get_table_info()
        #logging.debug(f"Database Schema: {schema}")
        return schema

    return (
        RunnablePassthrough.assign(schema=get_schema)
        | prompt
        | llm
        | StrOutputParser()
    )

def convert_name_to_email(name):
    # Split the name by space
    parts = name.split()
    # Check if the name contains two parts
    if len(parts) == 2:
        first_name, last_name = parts
        # Construct the email address
        email = f"{first_name.lower()}.{last_name.lower()}@email.com"
        #logging.debug(f"Converted name '{name}' to email '{email}'")
        return email
    return None

def format_chat_history(chat_history):
    formatted_history = ""
    for message in chat_history:
        if isinstance(message, HumanMessage):
            formatted_history += f"User: {message.content}\n"
        elif isinstance(message, AIMessage):
            formatted_history += f"Assistant: {message.content}\n"
    return formatted_history.strip()

def get_response(user_query: str, db: SQLDatabase, chat_history: list):
    #logging.debug(f"User Query: {user_query}")
    # Handle greetings separately
    greetings = ["hi", "hello", "hola", "good morning", "good afternoon", "good evening", "good night"]
    if user_query.lower() in greetings:
        return "Hello! How can I assist you today?"

    # Handle conversation separately
    conversations = ["ok", "thank you", "see you", "nice", "great"]
    if user_query.lower() in conversations:
        return "Can I help you with anything else?"

    # Handle goodbye separately
    goodbyes = ["goodbye", "bye", "ok bye"]
    if user_query.lower() in goodbyes:
        return "Goodbye!"

    # Process user query with Spacy to handle similar questions
    doc = nlp(user_query)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    #logging.debug(f"Extracted Entities: {entities}")

    # Check for user names in the entities
    for text, label in entities:
        if label == "PERSON":
            email = convert_name_to_email(text)
            if email:
                user_query = user_query.replace(text, email)
                #logging.debug(f"User query after name to email conversion: {user_query}")

    # Process the modified user query
    sql_chain = get_sql_chain(db)

    template = """
You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
Based on the table schema below, question, SQL query, and SQL response, provide a natural language response.

Use the SQL Response to give the answer. Convert the SQL response into natural language before presenting it. Do not print the SQL response in the output; only provide the natural language response.

If the SQL Response is a count (e.g., COUNT(*)), the natural language output should clearly and accurately state the count.

If the SQL response contains a single value (e.g., COUNT(*)), extract and use this value directly in the natural language response.

If there is no data available for any SQL query, then output "Data not found".

Do not print outputs in paragraph format. Do not print Conversation history in output; only print the final output that is converted to natural language from the SQL response.

Do not print extra information; only give the required information to the user.

Provide all natural language outputs in numbered or bullet list format.

<SCHEMA>
{schema}
</SCHEMA>

Question: {question}
SQL Query: <SQL>{query}</SQL>
SQL Response: {response}
"""
    prompt = ChatPromptTemplate.from_template(template)

    chain = (
        RunnablePassthrough.assign(query=sql_chain).assign(
            schema=lambda _: db.get_table_info(),
            response=lambda vars: db.run(vars["query"]),
        )
        | prompt
        | llm
        | StrOutputParser()
    )

    # Prepare variables for the chain
    formatted_history = format_chat_history(chat_history)
    variables = {
        "question": user_query,
        "chat_history": formatted_history,
    }
    #logging.debug(f"Chain Variables: {variables}")

    # Invoke the chain
    try:
        result = chain.invoke(variables)
        #logging.debug(f"Chain Result: {result}")
    except Exception as e:
        #logging.error(f"Error during chain invocation: {e}")
        result = "Sorry, an error occurred while processing your request."

    # Remove any leading/trailing whitespace and unnecessary prefixes
    result = result.strip()
    # If the result starts with "Bot:" or "Assistant:", remove it
    if result.startswith("Bot:"):
        result = result[len("Bot:"):].strip()
    if result.startswith("Assistant:"):
        result = result[len("Assistant:"):].strip()

    return result

def main():
    chat_history = [
        AIMessage(content="Hello! I'm a SQL Chatbot. Ask me anything about the database."),
    ]
    print("Bot: Hello! I'm a Oracle Database Chatbot. Ask me anything about the database.")
    db = SQLDatabase(engine)

    while True:
        user_query = input("You: ")
        if user_query.lower().strip() in ['exit', 'quit', 'bye']:
            print("Bot: Goodbye!")
            break
        if user_query.strip() == "":
            continue
        chat_history.append(HumanMessage(content=user_query))
        response = get_response(user_query, db, chat_history)
        print(f"Bot: {response}")
        chat_history.append(AIMessage(content=response))

if __name__ == "__main__":
    main()

