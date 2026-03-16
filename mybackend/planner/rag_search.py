# rag_chain.py
import json
import logging
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from django.conf import settings

logger = logging.getLogger(__name__)

def get_persist_dir():
    """Get the ChromaDB persistence directory from settings or use default."""
    return getattr(settings, 'CHROMA_PERSIST_DIR', 'chroma_db')

def get_rag_llm():
    """Get the LLM model name from settings or use default."""
    return getattr(settings, 'RAG_MODEL', 'gpt-3.5-turbo')

def get_embedding_model():
    """Get the embedding model from settings or use default."""
    return getattr(settings, 'RAG_EMBEDDING_MODEL', 'text-embedding-3-small')

def generate_plan(description: str) -> dict:
    """
    Generate a structured project plan from a free-form description.
    
    Args:
        description: Free-form user description of a project (e.g., "replace copper pipe with PEX")
    
    Returns:
        dict with keys:
            - materials: list of material objects with {name, quantity, unit, category}
            - tools: list of tool names needed
            - steps: list of step descriptions
            - warnings: list of safety/caution warnings
    
    Raises:
        Exception: if OpenAI API fails or vector store is inaccessible
    """
    try:
        persist_dir = get_persist_dir()
        embedding_model = get_embedding_model()
        
        # Initialize vector store
        vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=OpenAIEmbeddings(model=embedding_model),
        )
        retriever = vectorstore.as_retriever()
        
        # Format context from retrieved documents
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        # Create prompt for structured plan generation
        prompt = PromptTemplate.from_template(
            """You are an expert DIY home renovation assistant. Based on the following context only and the user's project description, 
            generate a detailed structured project plan. If not much relevant information is found in the context, provide a disclaimer 
            in the warnings section and generate a basic plan based on general knowledge.

            IMPORTANT: You MUST return ONLY valid JSON (no markdown, no extra text) with this exact structure:
            {{
                "materials": [
                    {{"name": "item name", "quantity": 2, "unit": "piece", "category": "pipe/fitting/other"}},
                    ...
                ],
                "tools": [
                    {{"name": "item name", "quantity": 1, "unit": "piece", "category": "tool"}},
                    ...
                ],
                "steps": ["Step 1: description", "Step 2: description", ...],
                "warnings": ["Safety warning 1", "Caution: warning 2", ...]
            }}
            If the something in the materials list is already mentioned in the tools list, do not include it again in the materials list.

            Context from knowledge base:
            {context}

            User's Project Description:
            {description}

            Generate the plan as valid JSON only:"""
        )
        
        llm = ChatOpenAI(model_name=get_rag_llm(), temperature=0)
        
        # Build the chain
        chain = (
            {
                "context": retriever | RunnableLambda(format_docs),
                "description": RunnablePassthrough(),
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        
        # Invoke the chain
        result_text = chain.invoke(description)
        logging.info("Result text from RAG chain: ", result_text)
        
        # Parse the JSON response
        # Try to extract JSON if it's wrapped in markdown code blocks
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        result_json = json.loads(result_text)
        
        # Validate and normalize the response structure
        plan = {
            "materials": result_json.get("materials", []),
            "tools": result_json.get("tools", []),
            "steps": result_json.get("steps", []),
            "warnings": result_json.get("warnings", []),
        }
        
        return plan
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse plan JSON: {e}")
        raise ValueError(f"Failed to parse plan response from AI model: {str(e)}")
    except Exception as e:
        logger.exception(f"Error generating plan: {e}")
        raise