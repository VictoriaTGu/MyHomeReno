"""
Unit tests for RAG (Retrieval-Augmented Generation) plan generation (Phase 3).

Tests the generate_plan() function with mocked LLM and vector store,
ensuring proper plan generation, JSON parsing, and error handling.
"""

import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from django.conf import settings
from langchain_core.messages import AIMessage

from planner.rag_search import generate_plan, get_rag_llm, get_embedding_model, get_persist_dir


class RAGConfigurationsTests(TestCase):
    """Test RAG configuration functions."""

    def test_get_persist_dir_default(self):
        """Test get_persist_dir returns default when not in settings."""
        with override_settings(**{k: v for k, v in settings.__dict__.items() if k != 'CHROMA_PERSIST_DIR'}):
            directory = get_persist_dir()
            self.assertEqual(directory, 'chroma_db')

    @override_settings(CHROMA_PERSIST_DIR='/custom/path')
    def test_get_persist_dir_custom(self):
        """Test get_persist_dir returns custom setting."""
        directory = get_persist_dir()
        self.assertEqual(directory, '/custom/path')

    def test_get_rag_llm_default(self):
        """Test get_rag_llm returns default model."""
        with override_settings(**{k: v for k, v in settings.__dict__.items() if k != 'RAG_MODEL'}):
            model = get_rag_llm()
            self.assertEqual(model, 'gpt-3.5-turbo')

    @override_settings(RAG_MODEL='gpt-4-turbo')
    def test_get_rag_llm_custom(self):
        """Test get_rag_llm returns custom model."""
        model = get_rag_llm()
        self.assertEqual(model, 'gpt-4-turbo')

    def test_get_embedding_model_default(self):
        """Test get_embedding_model returns default."""
        with override_settings(**{k: v for k, v in settings.__dict__.items() if k != 'RAG_EMBEDDING_MODEL'}):
            model = get_embedding_model()
            self.assertEqual(model, 'text-embedding-3-small')

    @override_settings(RAG_EMBEDDING_MODEL='text-embedding-3-large')
    def test_get_embedding_model_custom(self):
        """Test get_embedding_model returns custom model."""
        model = get_embedding_model()
        self.assertEqual(model, 'text-embedding-3-large')


class GeneratePlanTests(TestCase):
    """Test the generate_plan() function with mocked OpenAI API."""

    @patch('planner.rag_search.Chroma')
    @patch('planner.rag_search.ChatOpenAI')
    def test_generate_plan_success(self, mock_chat_openai, mock_chroma):
        """Test successful plan generation with valid response."""
        # Setup mock vector store
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [
            MagicMock(page_content='Copper pipe installation guide...'),
            MagicMock(page_content='PEX tubing best practices...'),
        ]
        mock_vectorstore = MagicMock()
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_chroma.return_value = mock_vectorstore

        # Setup mock LLM response
        mock_response_content = json.dumps({
            "materials": [
                {"name": "PEX tubing", "quantity": 50, "unit": "ft", "category": "pipe"},
                {"name": "Fitting connectors", "quantity": 4, "unit": "piece", "category": "fitting"},
            ],
            "tools": [
                {"name": "Adjustable wrench", "quantity": 1, "unit": "piece", "category": "tool"},
                {"name": "Crimping tool", "quantity": 1, "unit": "piece", "category": "tool"},
                {"name": "PEX cutter", "quantity": 1, "unit": "piece", "category": "tool"},
            ],
            "steps": [
                "Turn off water supply",
                "Remove old copper pipe",
                "Install PEX tubing",
                "Test for leaks",
            ],
            "warnings": [
                "Turn off water supply before starting",
                "Ensure proper crimping of connectors",
            ]
        })
        mock_llm = MagicMock(return_value=mock_response_content)
        mock_llm.invoke.return_value = mock_response_content
        mock_chat_openai.return_value = mock_llm

        # Execute
        result = generate_plan("Replace copper pipe with PEX under kitchen sink")

        # Verify structure
        self.assertIn('materials', result)
        self.assertIn('tools', result)
        self.assertIn('steps', result)
        self.assertIn('warnings', result)

        # Verify materials
        self.assertEqual(len(result['materials']), 2)
        self.assertEqual(result['materials'][0]['name'], 'PEX tubing')
        self.assertEqual(result['materials'][0]['quantity'], 50)
        self.assertEqual(result['materials'][0]['unit'], 'ft')
        self.assertEqual(result['materials'][0]['category'], 'pipe')

        # Verify tools
        self.assertEqual(len(result['tools']), 3)
        tool_names = [t['name'] for t in result['tools']]
        self.assertIn('Adjustable wrench', tool_names)
        self.assertEqual(result['tools'][0]['quantity'], 1)
        self.assertEqual(result['tools'][0]['category'], 'tool')

        # Verify steps
        self.assertEqual(len(result['steps']), 4)
        self.assertTrue(result['steps'][0].startswith('Turn off'))

        # Verify warnings
        self.assertEqual(len(result['warnings']), 2)

    @patch('planner.rag_search.Chroma')
    @patch('planner.rag_search.ChatOpenAI')
    def test_generate_plan_with_markdown_code_blocks(self, mock_chat_openai, mock_chroma):
        """Test plan generation when LLM wraps response in markdown code blocks."""
        mock_vectorstore = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [MagicMock(page_content='Sample content')]
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_chroma.return_value = mock_vectorstore

        # LLM response wrapped in markdown code blocks
        valid_json = {
            "materials": [{"name": "Test", "quantity": 1, "unit": "piece", "category": "other"}],
            "tools": [{"name": "Test tool", "quantity": 1, "unit": "piece", "category": "tool"}],
            "steps": ["Test step"],
            "warnings": ["Test warning"]
        }
        mock_response_content = f"```json\n{json.dumps(valid_json)}\n```"
        mock_llm = MagicMock(return_value=mock_response_content)
        mock_llm.invoke.return_value = mock_response_content
        mock_chat_openai.return_value = mock_llm

        result = generate_plan("Test project")

        self.assertEqual(len(result['materials']), 1)
        self.assertEqual(result['materials'][0]['name'], 'Test')
        self.assertEqual(len(result['tools']), 1)
        self.assertEqual(result['tools'][0]['name'], 'Test tool')

    @patch('planner.rag_search.Chroma')
    @patch('planner.rag_search.ChatOpenAI')
    def test_generate_plan_invalid_json_raises_error(self, mock_chat_openai, mock_chroma):
        """Test that invalid JSON from LLM raises ValueError."""
        mock_vectorstore = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [MagicMock(page_content='Sample content')]
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_chroma.return_value = mock_vectorstore

        # Invalid JSON response
        mock_llm = MagicMock(return_value="This is not JSON at all")
        mock_llm.invoke.return_value = "This is not JSON at all"
        mock_chat_openai.return_value = mock_llm

        with self.assertRaises(ValueError) as context:
            generate_plan("Test project")
        
        self.assertIn('Failed to parse plan response', str(context.exception))

    @patch('planner.rag_search.Chroma')
    @patch('planner.rag_search.ChatOpenAI')
    def test_generate_plan_empty_lists_handled(self, mock_chat_openai, mock_chroma):
        """Test plan generation with empty materials/tools/steps/warnings."""
        mock_vectorstore = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [MagicMock(page_content='Sample content')]
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_chroma.return_value = mock_vectorstore

        mock_response = {
            "materials": [],
            "tools": [],
            "steps": [],
            "warnings": []
        }
        
        mock_llm = MagicMock(return_value=json.dumps(mock_response))
        mock_llm.invoke.return_value = json.dumps(mock_response)
        mock_chat_openai.return_value = mock_llm

        result = generate_plan("Test project")

        self.assertEqual(result['materials'], [])
        self.assertEqual(result['tools'], [])
        self.assertEqual(result['steps'], [])
        self.assertEqual(result['warnings'], [])

    @patch('planner.rag_search.Chroma')
    @patch('planner.rag_search.ChatOpenAI')
    def test_generate_plan_uses_configured_models(self, mock_chat_openai, mock_chroma):
        """Test that generate_plan uses settings-configured LLM and embedding models."""
        with override_settings(RAG_MODEL='gpt-4-turbo', RAG_EMBEDDING_MODEL='text-embedding-3-large'):
            mock_vectorstore = MagicMock()
            mock_retriever = MagicMock()
            mock_retriever.invoke.return_value = [MagicMock(page_content='Sample content')]
            mock_vectorstore.as_retriever.return_value = mock_retriever
            mock_chroma.return_value = mock_vectorstore

            mock_response = {
                "materials": [],
                "tools": [],
                "steps": [],
                "warnings": []
            }
            
            mock_llm = MagicMock(return_value=json.dumps(mock_response))
            mock_llm.invoke.return_value = json.dumps(mock_response)
            mock_chat_openai.return_value = mock_llm

            result = generate_plan("Test project")

            # Verify ChatOpenAI was called with configured model
            call_kwargs = mock_chat_openai.call_args[1]
            self.assertEqual(call_kwargs['model_name'], 'gpt-4-turbo')

    @patch('planner.rag_search.Chroma')
    @patch('planner.rag_search.ChatOpenAI')
    def test_generate_plan_handles_chroma_exception(self, mock_chat_openai, mock_chroma):
        """Test error handling when ChromaDB raises exception."""
        mock_chroma.side_effect = Exception("ChromaDB connection failed")

        with self.assertRaises(Exception):
            generate_plan("Test project")

    @patch('planner.rag_search.Chroma')
    @patch('planner.rag_search.ChatOpenAI')
    def test_generate_plan_handles_openai_exception(self, mock_chat_openai, mock_chroma):
        """Test error handling when OpenAI API raises exception."""
        mock_vectorstore = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [MagicMock(page_content='Sample content')]
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_chroma.return_value = mock_vectorstore

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("OpenAI API error")
        mock_chat_openai.return_value = mock_llm

        with self.assertRaises(Exception):
            generate_plan("Test project")

    @patch('planner.rag_search.Chroma')
    @patch('planner.rag_search.ChatOpenAI')
    def test_generate_plan_with_complex_materials(self, mock_chat_openai, mock_chroma):
        """Test handling of complex material and tool lists with various units."""
        mock_vectorstore = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [MagicMock(page_content='Sample content')]
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_chroma.return_value = mock_vectorstore

        mock_response = {
            "materials": [
                {"name": "PEX tubing", "quantity": 50, "unit": "ft", "category": "pipe"},
                {"name": "Crimping tool", "quantity": 1, "unit": "piece", "category": "tool"},
                {"name": "Wire nuts", "quantity": 10, "unit": "pack", "category": "connector"},
                {"name": "Electrical tape", "quantity": 2, "unit": "roll", "category": "consumable"},
            ],
            "tools": [
                {"name": "Adjustable wrench", "quantity": 1, "unit": "piece", "category": "tool"},
                {"name": "Crimper", "quantity": 1, "unit": "piece", "category": "tool"},
                {"name": "Wire cutter", "quantity": 1, "unit": "piece", "category": "tool"},
            ],
            "steps": ["Step 1", "Step 2"],
            "warnings": ["Warning 1"]
        }
        
        mock_llm = MagicMock(return_value=json.dumps(mock_response))
        mock_llm.invoke.return_value = json.dumps(mock_response)
        mock_chat_openai.return_value = mock_llm

        result = generate_plan("Complex project")

        self.assertEqual(len(result['materials']), 4)
        self.assertEqual(result['materials'][3]['unit'], 'roll')
        self.assertEqual(result['materials'][3]['category'], 'consumable')
        
        self.assertEqual(len(result['tools']), 3)
        self.assertEqual(result['tools'][0]['name'], 'Adjustable wrench')
        self.assertEqual(result['tools'][0]['category'], 'tool')

    @patch('planner.rag_search.Chroma')
    @patch('planner.rag_search.ChatOpenAI')
    def test_generate_plan_preserves_all_keys(self, mock_chat_openai, mock_chroma):
        """Test that response preserves all required keys even if missing."""
        mock_vectorstore = MagicMock()
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [MagicMock(page_content='Sample content')]
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_chroma.return_value = mock_vectorstore

        # Response missing some keys
        mock_response = {
            "materials": [{"name": "Item", "quantity": 1, "unit": "piece", "category": "other"}],
            # Missing tools, steps, warnings
        }
        
        mock_llm = MagicMock(return_value=json.dumps(mock_response))
        mock_llm.invoke.return_value = json.dumps(mock_response)
        mock_chat_openai.return_value = mock_llm

        result = generate_plan("Test project")

        # Verify all keys exist
        self.assertIn('materials', result)
        self.assertIn('tools', result)
        self.assertIn('steps', result)
        self.assertIn('warnings', result)
        
        # Verify missing keys default to empty lists
        self.assertEqual(result['tools'], [])
        self.assertEqual(result['steps'], [])
        self.assertEqual(result['warnings'], [])
