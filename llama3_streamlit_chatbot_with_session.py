import streamlit as st
from llama_index.core.llms import ChatMessage
import logging
import time
from llama_index.llms.ollama import Ollama
import requests
import json

#Logging info for DEV environment
logging.basicConfig(level=logging.INFO)

# Initialize chat history in session state if not already present
if 'messages' not in st.session_state:
    st.session_state.messages = []

#Get the list of models deployed on Ollama
def get_models():
    response = requests.get("http://localhost:11434/api/tags")
    if response is not None:
        #print(response)
        response_bytes = response.content
        data_str = response_bytes.decode('utf-8')  # decode bytes to string
        data = json.loads(data_str)  # parse JSON from string
        models =  []
        for key, value in data.items():
             print(f"{key}: {value}")
             models_resp = data['models']
             for model in models_resp:
                 models.append(model['name'])
        return models
        print(f" Response Model names :"+str(models))

# Function to chat with LLM with streaming on selected a model
def prepare_chat(model, messages):
    try:
        # Initialize the language model with a timeout
        llm = Ollama(model=model, request_timeout=180.0) 
        # Stream chat responses from the model
        resp = llm.stream_chat(messages)
        response = ""
        response_placeholder = st.empty()
        # Append each piece of the response to the output
        for r in resp:
            response += r.delta
            response_placeholder.write(response)
        # Log the interaction details
        logging.info(f"Model: {model}, Messages: {messages}, Response: {response}")
        return response
    except Exception as e:
        # Log and re-raise any errors that occur
        logging.error(f"Error during streaming: {str(e)}")
        raise e

#Main function for UI display
def main():
    #Title of the App
    st.title(":rainbow[Local LLM Client for Multiple Model Chat]")  
    logging.info("App started")  # Log that the app has started
    #Select a models from available deployed models 
    model = st.selectbox("Select a model", get_models())
    logging.info(f"Selected Model: {model}")
    st.subheader(f":rainbow[Selected Model: {model}]")  # Set the title of the Streamlit app

    # Prompt for user input and save to chat history
    if prompt := st.chat_input("Enter your prompt"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        logging.info(f"User input: {prompt}")

        # Display the user's prompt
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Generate a new response if the last message is not from the assistant
        if st.session_state.messages[-1]["role"] != "assistant":
            with st.chat_message("assistant"):
                start_time = time.time()  # Start timing the response generation
                logging.info("Generating response")

                with st.spinner("Generating response..."):
                    try:
                        # Prepare messages for the LLM and stream the response
                        messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in st.session_state.messages]
                        response_message = prepare_chat(model, messages) #Calling LLM chat_chat function
                        duration = time.time() - start_time  # Calculate the duration
                        response_message_with_duration = f"{response_message}\n\nDuration: {duration:.2f} seconds"
                        st.session_state.messages.append({"role": "assistant", "content": response_message_with_duration})
                        st.write(f":blue[Response duration: {duration:.2f} seconds]")
                        logging.info(f"Response: {response_message}, Duration: {duration:.2f} s")

                    except Exception as e:
                        # Handle errors and display an error message
                        st.session_state.messages.append({"role": "assistant", "content": str(e)})
                        st.error("An error occurred while generating the response.")
                        logging.error(f"Error: {str(e)}")

#call the main function
if __name__ == "__main__":
    main()