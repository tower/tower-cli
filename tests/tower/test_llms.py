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
    context.inference_provider = "ollama"
    context.inference_router_api_key = None
    return context

@pytest.fixture
def mock_hf_together_context():
    """Create a mock TowerContext for Hugging Face Hub testing."""
    context = MagicMock(spec=TowerContext)
    context.is_local.return_value = False
    context.inference_router = "hugging_face_hub"
    context.inference_router_api_key = os.getenv("TOWER_INFERENCE_ROUTER_API_KEY")
    context.inference_provider = "together"
    return context

@pytest.fixture
def mock_hf_context():
    """Create a mock TowerContext for Hugging Face Hub testing."""
    context = MagicMock(spec=TowerContext)
    context.is_local.return_value = False
    context.inference_router = "hugging_face_hub"
    context.inference_router_api_key = os.getenv("TOWER_INFERENCE_ROUTER_API_KEY")
    context.inference_provider = None
    return context


@pytest.fixture
def mock_ollama_response():
    """Create a mock Ollama response."""
    response = MagicMock()
    response.message.content = "This is a test response"
    return response

@pytest.mark.skip(reason="Not runnable right now in GH Actions")
def test_llms_nameres_with_model_family_locally_1(mock_ollama_context):
    """
    Test resolving a model family name to a particular model.
    Run this test with ollama locally installed.
    deepseek-r1 is a name that is used by both ollama and HF
    """
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_ollama_context):
            
        # Create LLM instance based on model family name
        llm = llms("deepseek-r1")
            
        # Verify it's an Llm instance
        assert isinstance(llm, Llm)

        # Verify the resolved model was found locally
        assert llm.model_name.startswith("deepseek-r1:")
            
@pytest.mark.skip(reason="Not runnable right now in GH Actions")
def test_llms_nameres_with_model_family_on_hugging_face_hub_1(mock_hf_together_context):
    """
    Test resolving a model family name to a particular model.
    Run this test against models available on Hugging Face Hub.
    deepseek-r1 is a name that is used by both ollama and HF
    """
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_hf_together_context):
            
        assert mock_hf_together_context.inference_router_api_key is not None
        
        # Create LLM instance
        llm = llms("deepseek-r1")
            
        # Verify it's an Llm instance
        assert isinstance(llm, Llm)

        # Verify the resolved model was found on the Hub
        assert llm.model_name.startswith("deepseek-ai")
            
@pytest.mark.skip(reason="Not runnable right now in GH Actions")
def test_llms_nameres_with_model_family_locally_2(mock_ollama_context):
    """
    Test resolving a model family name to a particular model.
    Run this test with ollama locally installed.
    llama3.2 is a name used by ollama.
    Llama-3.2 is a name used on HF.
    """
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_ollama_context):
        
        # Create LLM instance based on model family name
        llm = llms("llama3.2")
            
        # Verify it's an Llm instance
        assert isinstance(llm, Llm)

        # Verify the resolved model was found locally
        assert llm.model_name.startswith("llama3.2:")
            
@pytest.mark.skip(reason="Not runnable right now in GH Actions")
def test_llms_nameres_with_model_family_on_hugging_face_hub_2(mock_hf_together_context):
    """
    Test resolving a model family name to a particular model.
    Run this test against models available on Hugging Face Hub.
    llama3.2 is a name used by ollama.
    Llama-3.2 is a name used on HF.
    """
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_hf_together_context):

        assert mock_hf_together_context.inference_router_api_key is not None
        
        # Create LLM instance
        llm = llms("llama3.2")
            
        # Verify it's an Llm instance
        assert isinstance(llm, Llm)

        # Verify the resolved model was found on the Hub
        assert "llama" in llm.model_name


@pytest.mark.skip(reason="Not runnable right now in GH Actions")
def test_llms_nameres_with_nonexistent_model_locally(mock_ollama_context):
    """Test llms function with a model that doesn't exist locally."""
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_ollama_context):
        # Mock get_local_ollama_models to return empty list
        with patch('tower._llms.get_local_ollama_models', return_value=[]):
            # Test with a non-existent model
            with pytest.raises(ValueError) as exc_info:
                llm = llms("nonexistent-model")
            
            # Verify the error message
            assert "No models found" in str(exc_info.value)


@pytest.mark.skip(reason="Not runnable right now in GH Actions")
def test_llms_nameres_with_nonexistent_model_on_hugging_face_hub(mock_hf_together_context):
    """Test llms function with a model that doesn't exist on huggingface hub."""
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_hf_together_context):

        with pytest.raises(ValueError) as exc_info:
            llm = llms("nonexistent-model")
            
        # Verify the error message
        assert "No models found" in str(exc_info.value)


@pytest.mark.skip(reason="Not runnable right now in GH Actions")
def test_llms_nameres_with_exact_model_name_on_hugging_face_hub(mock_hf_together_context):
    """Test specifying the exact name of a model on Hugging Face Hub."""
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_hf_together_context):
        
        assert mock_hf_together_context.inference_router_api_key is not None
        
        # Create LLM instance
        llm = llms("deepseek-ai/DeepSeek-R1")
            
        # Verify it's an Llm instance
        assert isinstance(llm, Llm)

        # Verify the context was set
        assert llm.context == mock_hf_together_context
            
        # Verify the resolved model was found on the Hub
        assert llm.model_name.startswith("deepseek-ai/DeepSeek-R1")

@pytest.mark.skip(reason="Not runnable right now in GH Actions")
def test_llms_nameres_with_partial_model_name_on_hugging_face_hub(mock_hf_context):
    """Test specifying a partial model name on Hugging Face Hub."""
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_hf_context):
            
        assert mock_hf_context.inference_router_api_key is not None
        
        # Create LLM instance
        llm = llms("google/gemma-3")
            
        # Verify it's an Llm instance
        assert isinstance(llm, Llm)

        # Verify the context was set
        assert llm.context == mock_hf_context

        # Verify the resolved model was found on the Hub
        assert llm.model_name.startswith("google/gemma-3")

@pytest.mark.skip(reason="Not runnable right now in GH Actions")
def test_llms_inference_with_hugging_face_hub_1(mock_hf_together_context):
    """Test actual inference on a model served by together via Hugging Face Hub."""
    # Mock the TowerContext.build() to return our mock context
    with patch('tower._llms.TowerContext.build', return_value=mock_hf_together_context):
            
        assert mock_hf_together_context.inference_router_api_key is not None
        
        # Create LLM instance
        llm = llms("deepseek-ai/DeepSeek-R1")
            
        # Test a simple prompt
        response = llm.prompt("What is your model name?")
        assert "DeepSeek-R1" in response
            
@pytest.mark.skip(reason="Not runnable right now in GH Actions")
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
            





