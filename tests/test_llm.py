import os
import pytest
from unittest.mock import patch
from agents.llm import get_llm

def test_get_llm_missing_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY not set"):
        get_llm()

@patch("agents.llm.ChatGroq")
def test_get_llm_success(mock_chatgroq, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_MODEL", "test-model")
    
    llm = get_llm()
    
    mock_chatgroq.assert_called_once_with(
        api_key="test-key",
        model="test-model",
        temperature=0,
    )
    assert llm == mock_chatgroq.return_value
