import os
import pytest
from unittest.mock import patch, MagicMock

from tower._llms import llms, Llm
from tower._context import TowerContext

@pytest.fixture
def mock_ollama_context():
    """Create a mock TowerContext for testing."""
    context = MagicMock(spec=TowerContext)
    context.is_local.return_value = True
    context.inference_router = "ollama"
    context.inference_service = "ollama"
    context.inference_router_api_key = None
    return context

@pytest.fixture
def mock_hf_together_context():
    """Create a mock TowerContext for Hugging Face Hub testing."""
    context = MagicMock(spec=TowerContext)
    context.is_local.return_value = False
    context.inference_router = "hugging_face_hub"
    context.inference_router_api_key = os.getenv("TOWER_INFERENCE_ROUTER_API_KEY")
    context.inference_service = "together"
    return context

@pytest.fixture
def mock_hf_context():
    """Create a mock TowerContext for Hugging Face Hub testing."""
    context = MagicMock(spec=TowerContext)
    context.is_local.return_value = False
    context.inference_router = "hugging_face_hub"
    context.inference_router_api_key = os.getenv("TOWER_INFERENCE_ROUTER_API_KEY")
    context.inference_service = None
    return context


@pytest.fixture
def mock_ollama_response():
    """Create a mock Ollama response."""
    response = MagicMock()
    response.message.content = "This is a test response"
    return response

def test_llms_nameres_with_model_family_locally_1(mock_ollama_context, mock_ollama_response):
    """
    Test resolving a model family name to a particular model.
    Run this test with ollama locally installed.
    deepseek-r1 is a name that is used by both ollama and HF
    """
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_ollama_context):
        # Mock the chat function to return our mock response
        with patch('tower._llms.chat', return_value=mock_ollama_response):
            
            # Create LLM instance based on model family name
            llm = llms("deepseek-r1")
            
            # Verify it's an Llm instance
            assert isinstance(llm, Llm)

            # Verify the resolved model was found locally
            assert llm.model_name.startswith("deepseek-r1:")
            
def test_llms_nameres_with_model_family_on_hugging_face_hub_1(mock_hf_together_context):
    """
    Test resolving a model family name to a particular model.
    Run this test against models available on Hugging Face Hub.
    deepseek-r1 is a name that is used by both ollama and HF
    """
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_hf_together_context):
        
        with patch('tower._llms.InferenceClient') as mock_client:
            
            # Create LLM instance
            llm = llms("deepseek-r1")
            
            # Verify it's an Llm instance
            assert isinstance(llm, Llm)

            # Verify the resolved model was found on the Hub
            assert llm.model_name.startswith("deepseek-ai")
            

def test_llms_nameres_with_model_family_locally_2(mock_ollama_context, mock_ollama_response):
    """
    Test resolving a model family name to a particular model.
    Run this test with ollama locally installed.
    llama3.2 is a name used by ollama.
    Llama-3.2 is a name used on HF.
    """
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_ollama_context):
        # Mock the chat function to return our mock response
        with patch('tower._llms.chat', return_value=mock_ollama_response):
            
            # Create LLM instance based on model family name
            llm = llms("llama3.2")
            
            # Verify it's an Llm instance
            assert isinstance(llm, Llm)

            # Verify the resolved model was found locally
            assert llm.model_name.startswith("llama3.2:")
            
def test_llms_nameres_with_model_family_on_hugging_face_hub_2(mock_hf_together_context):
    """
    Test resolving a model family name to a particular model.
    Run this test against models available on Hugging Face Hub.
    llama3.2 is a name used by ollama.
    Llama-3.2 is a name used on HF.
    """
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_hf_together_context):
        
        with patch('tower._llms.InferenceClient') as mock_client:
            
            # Create LLM instance
            llm = llms("llama3.2")
            
            # Verify it's an Llm instance
            assert isinstance(llm, Llm)

            # Verify the resolved model was found on the Hub
            assert "llama" in llm.model_name



def test_llms_nameres_with_nonexistent_model_locally(mock_ollama_context):
    """Test llms function with a model that doesn't exist locally."""
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_ollama_context):
        # Mock get_local_ollama_models to return empty list
        with patch('tower._llms.get_local_ollama_models', return_value=[]):
            # Test with a non-existent model
            with pytest.raises(ValueError) as exc_info:
                llms("nonexistent-model")
            
            # Verify the error message
            assert "Model nonexistent-model is not available" in str(exc_info.value)

def test_llms_nameres_with_exact_model_name_on_hugging_face_hub(mock_hf_together_context):
    """Test finding a particular model on Hugging Face Hub."""
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_hf_together_context):
        # Mock the Hugging Face Hub client
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="This is a test response"))]
        
        with patch('tower._llms.InferenceClient') as mock_client:
            mock_client.return_value.chat_completion.return_value = mock_completion
            
            # Create LLM instance
            llm = llms("deepseek-ai/DeepSeek-R1")
            
            # Verify it's an Llm instance
            assert isinstance(llm, Llm)

            # Verify the context was set
            assert llm.context == mock_hf_together_context

            # Test a simple prompt
            response = llm.prompt("Hello, how are you?")
            assert response == "This is a test response"
            
            # Verify the resolved model was found on the Hub
            assert llm.model_name.startswith("deepseek-ai/DeepSeek-R1")


def test_llms_inference_with_hugging_face_hub_1(mock_hf_together_context):
    """Test actual inference on a model served by together via Hugging Face Hub."""
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_hf_together_context):
            
        # Create LLM instance
        llm = llms("deepseek-ai/DeepSeek-R1")
            
        # Test a simple prompt
        response = llm.prompt("What is your model name?")
        assert "DeepSeek-R1" in response
            

def test_llms_inference_locally_1(mock_ollama_context, mock_ollama_response):
    """Test local inference, but against a stubbed response."""
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_ollama_context):
        # Mock the chat function to return our mock response
        with patch('tower._llms.chat', return_value=mock_ollama_response):
            
            # Create LLM instance based on model family name
            llm = llms("deepseek-r1")
            
            # Test a simple prompt
            response = llm.prompt("Hello, how are you?")
            assert response == "This is a test response"
            


def test_llms_nameres_with_partial_model_name_on_hugging_face_hub(mock_hf_context):
    """Test llms function with Hugging Face Hub inference."""
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_hf_context):
            
        # Create LLM instance
        llm = llms("google/gemma-3")
            
        # Verify it's an Llm instance
        assert isinstance(llm, Llm)

        # Verify the context was set
        assert llm.context == mock_hf_context

        # Verify the resolved model was found on the Hub
        assert llm.model_name.startswith("google/gemma-3")



