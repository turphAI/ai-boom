"""
Tests for AWS Lambda handlers.

This module tests the Lambda handler functions for all scrapers,
including timeout handling, error scenarios, and chunked processing.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import handlers
from handlers.bond_issuance_handler import lambda_handler as bond_handler
from handlers.bond_issuance_handler import chunked_execution_handler as bond_chunked_handler
from handlers.bdc_discount_handler import lambda_handler as bdc_handler
from handlers.bdc_discount_handler import chunked_execution_handler as bdc_chunked_handler
from handlers.credit_fund_handler import lambda_handler as credit_handler
from handlers.credit_fund_handler import chunked_execution_handler as credit_chunked_handler
from handlers.bank_provision_handler import lambda_handler as bank_handler
from handlers.bank_provision_handler import chunked_execution_handler as bank_chunked_handler


class MockContext:
    """Mock AWS Lambda context for testing."""
    
    def __init__(self, request_id="test-123", remaining_time=900000, memory_limit=1024):
        self.aws_request_id = request_id
        self._remaining_time = remaining_time
        self.memory_limit_in_mb = memory_limit
    
    def get_remaining_time_in_millis(self):
        return self._remaining_time


@pytest.fixture
def mock_context():
    """Fixture providing a mock Lambda context."""
    return MockContext()


@pytest.fixture
def cloudwatch_event():
    """Fixture providing a CloudWatch Events event."""
    return {
        "source": "aws.events",
        "detail-type": "Scheduled Event",
        "detail": {
            "scraper_name": "test-scraper"
        }
    }


class TestBondIssuanceHandler:
    """Tests for bond issuance Lambda handler."""
    
    @patch('handlers.bond_issuance_handler.BondIssuanceScraper')
    def test_successful_execution(self, mock_scraper_class, mock_context, cloudwatch_event):
        """Test successful bond issuance scraper execution."""
        # Setup mock scraper
        mock_scraper = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.data_source = "bond_issuance"
        mock_result.metric_name = "weekly"
        mock_result.timestamp = datetime.utcnow()
        mock_result.data = {
            'value': 5000000000,
            'metadata': {
                'companies': ['MSFT', 'META'],
                'bond_count': 2
            },
            'confidence': 0.95
        }
        
        mock_scraper.execute.return_value = mock_result
        mock_scraper_class.return_value = mock_scraper
        
        # Execute handler
        response = bond_handler(cloudwatch_event, mock_context)
        
        # Assertions
        assert response['statusCode'] == 200
        assert response['body']['success'] is True
        assert response['body']['data_source'] == "bond_issuance"
        assert 'data_summary' in response['body']
        assert response['body']['data_summary']['total_issuance'] == 5000000000
        assert response['body']['data_summary']['companies_count'] == 2
        
        # Verify scraper was called
        mock_scraper_class.assert_called_once()
        mock_scraper.execute.assert_called_once()
    
    @patch('handlers.bond_issuance_handler.BondIssuanceScraper')
    def test_scraper_failure(self, mock_scraper_class, mock_context, cloudwatch_event):
        """Test handler response when scraper fails."""
        # Setup mock scraper to fail
        mock_scraper = Mock()
        mock_result = Mock()
        mock_result.success = False
        mock_result.error = "Failed to fetch SEC data"
        mock_result.data_source = "bond_issuance"
        mock_result.metric_name = "weekly"
        mock_result.timestamp = datetime.utcnow()
        
        mock_scraper.execute.return_value = mock_result
        mock_scraper_class.return_value = mock_scraper
        
        # Execute handler
        response = bond_handler(cloudwatch_event, mock_context)
        
        # Assertions
        assert response['statusCode'] == 500
        assert response['body']['success'] is False
        assert response['body']['error'] == "Failed to fetch SEC data"
    
    @patch('handlers.bond_issuance_handler.BondIssuanceScraper')
    def test_timeout_handling(self, mock_scraper_class, mock_context, cloudwatch_event):
        """Test timeout handling in bond issuance handler."""
        # Setup context with very short timeout
        mock_context._remaining_time = 1000  # 1 second
        
        # Setup mock scraper to take too long
        mock_scraper = Mock()
        mock_scraper.execute.side_effect = lambda: __import__('time').sleep(2)
        mock_scraper_class.return_value = mock_scraper
        
        # Execute handler (should timeout)
        response = bond_handler(cloudwatch_event, mock_context)
        
        # Assertions
        assert response['statusCode'] == 408
        assert response['body']['success'] is False
        assert 'timeout' in response['body']['error'].lower()
    
    @patch('handlers.bond_issuance_handler.BondIssuanceScraper')
    def test_unexpected_exception(self, mock_scraper_class, mock_context, cloudwatch_event):
        """Test handling of unexpected exceptions."""
        # Setup mock scraper to raise exception
        mock_scraper_class.side_effect = ValueError("Unexpected error")
        
        # Execute handler
        response = bond_handler(cloudwatch_event, mock_context)
        
        # Assertions
        assert response['statusCode'] == 500
        assert response['body']['success'] is False
        assert 'Unexpected error' in response['body']['error']
        assert response['body']['error_type'] == 'ValueError'
    
    @patch('handlers.bond_issuance_handler.BondIssuanceScraper')
    def test_chunked_execution(self, mock_scraper_class, mock_context):
        """Test chunked execution handler."""
        # Setup chunked event
        chunked_event = {
            'chunk_size': 2,
            'chunk_index': 0
        }
        
        # Setup mock scraper
        mock_scraper = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = {
            'value': 2000000000,
            'metadata': {'bond_count': 1}
        }
        
        mock_scraper.execute.return_value = mock_result
        mock_scraper_class.return_value = mock_scraper
        
        # Execute chunked handler
        response = bond_chunked_handler(chunked_event, mock_context)
        
        # Assertions
        assert response['statusCode'] == 200
        assert response['body']['success'] is True
        assert response['body']['chunk_index'] == 0
        assert 'has_more_chunks' in response['body']
        assert 'companies_processed' in response['body']


class TestBDCDiscountHandler:
    """Tests for BDC discount Lambda handler."""
    
    @patch('handlers.bdc_discount_handler.BDCDiscountScraper')
    def test_successful_execution(self, mock_scraper_class, mock_context, cloudwatch_event):
        """Test successful BDC discount scraper execution."""
        # Setup mock scraper
        mock_scraper = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.data_source = "bdc_discount"
        mock_result.metric_name = "discount_to_nav"
        mock_result.timestamp = datetime.utcnow()
        mock_result.data = {
            'value': -0.15,
            'average_discount_percentage': -15.0,
            'bdc_count': 4,
            'metadata': {
                'symbols_processed': ['ARCC', 'OCSL', 'MAIN', 'PSEC']
            }
        }
        
        mock_scraper.execute.return_value = mock_result
        mock_scraper_class.return_value = mock_scraper
        
        # Execute handler
        response = bdc_handler(cloudwatch_event, mock_context)
        
        # Assertions
        assert response['statusCode'] == 200
        assert response['body']['success'] is True
        assert response['body']['data_source'] == "bdc_discount"
        assert 'data_summary' in response['body']
        assert response['body']['data_summary']['average_discount'] == -0.15
        assert response['body']['data_summary']['bdc_count'] == 4
    
    @patch('handlers.bdc_discount_handler.BDCDiscountScraper')
    def test_chunked_execution_all_processed(self, mock_scraper_class, mock_context):
        """Test chunked execution when all chunks are processed."""
        # Setup chunked event for chunk beyond available data
        chunked_event = {
            'chunk_size': 2,
            'chunk_index': 10  # Beyond available BDCs
        }
        
        mock_scraper = Mock()
        mock_scraper.BDC_CONFIG = {'ARCC': {}, 'OCSL': {}}  # Only 2 BDCs
        mock_scraper_class.return_value = mock_scraper
        
        # Execute chunked handler
        response = bdc_chunked_handler(chunked_event, mock_context)
        
        # Assertions
        assert response['statusCode'] == 200
        assert response['body']['success'] is True
        assert 'All chunks processed' in response['body']['message']


class TestCreditFundHandler:
    """Tests for credit fund Lambda handler."""
    
    @patch('handlers.credit_fund_handler.CreditFundScraper')
    def test_successful_execution(self, mock_scraper_class, mock_context, cloudwatch_event):
        """Test successful credit fund scraper execution."""
        # Setup mock scraper
        mock_scraper = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.data_source = "credit_fund"
        mock_result.metric_name = "gross_asset_value"
        mock_result.timestamp = datetime.utcnow()
        mock_result.data = {
            'value': 45000000000,
            'total_gross_assets': 180000000000,
            'funds_processed': 4,
            'confidence': 0.95
        }
        
        mock_scraper.execute.return_value = mock_result
        mock_scraper_class.return_value = mock_scraper
        
        # Execute handler
        response = credit_handler(cloudwatch_event, mock_context)
        
        # Assertions
        assert response['statusCode'] == 200
        assert response['body']['success'] is True
        assert response['body']['data_source'] == "credit_fund"
        assert 'data_summary' in response['body']
        assert response['body']['data_summary']['average_gross_assets'] == 45000000000
        assert response['body']['data_summary']['funds_processed'] == 4


class TestBankProvisionHandler:
    """Tests for bank provision Lambda handler."""
    
    @patch('handlers.bank_provision_handler.BankProvisionScraper')
    def test_successful_execution(self, mock_scraper_class, mock_context, cloudwatch_event):
        """Test successful bank provision scraper execution."""
        # Setup mock scraper
        mock_scraper = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.data_source = "bank_provision"
        mock_result.metric_name = "non_bank_financial_provisions"
        mock_result.timestamp = datetime.utcnow()
        mock_result.data = {
            'value': 1500000000,
            'bank_count': 6,
            'metadata': {
                'quarter': 'Q1 2024',
                'extraction_methods': {'xbrl': 4, 'transcript': 2}
            },
            'confidence': 0.85
        }
        
        mock_scraper.execute.return_value = mock_result
        mock_scraper_class.return_value = mock_scraper
        
        # Execute handler
        response = bank_handler(cloudwatch_event, mock_context)
        
        # Assertions
        assert response['statusCode'] == 200
        assert response['body']['success'] is True
        assert response['body']['data_source'] == "bank_provision"
        assert 'data_summary' in response['body']
        assert response['body']['data_summary']['total_provisions'] == 1500000000
        assert response['body']['data_summary']['bank_count'] == 6
        assert response['body']['data_summary']['quarter'] == 'Q1 2024'


class TestErrorHandling:
    """Tests for error handling across all handlers."""
    
    @pytest.mark.parametrize("handler_func,scraper_class", [
        (bond_handler, 'handlers.bond_issuance_handler.BondIssuanceScraper'),
        (bdc_handler, 'handlers.bdc_discount_handler.BDCDiscountScraper'),
        (credit_handler, 'handlers.credit_fund_handler.CreditFundScraper'),
        (bank_handler, 'handlers.bank_provision_handler.BankProvisionScraper'),
    ])
    def test_import_error_handling(self, handler_func, scraper_class, mock_context, cloudwatch_event):
        """Test handling of import errors."""
        with patch(scraper_class, side_effect=ImportError("Module not found")):
            response = handler_func(cloudwatch_event, mock_context)
            
            assert response['statusCode'] == 500
            assert response['body']['success'] is False
            assert 'Module not found' in response['body']['error']
    
    @pytest.mark.parametrize("handler_func,scraper_class", [
        (bond_handler, 'handlers.bond_issuance_handler.BondIssuanceScraper'),
        (bdc_handler, 'handlers.bdc_discount_handler.BDCDiscountScraper'),
        (credit_handler, 'handlers.credit_fund_handler.CreditFundScraper'),
        (bank_handler, 'handlers.bank_provision_handler.BankProvisionScraper'),
    ])
    def test_connection_error_handling(self, handler_func, scraper_class, mock_context, cloudwatch_event):
        """Test handling of connection errors."""
        with patch(scraper_class) as mock_scraper_class:
            mock_scraper = Mock()
            mock_scraper.execute.side_effect = ConnectionError("Network unreachable")
            mock_scraper_class.return_value = mock_scraper
            
            response = handler_func(cloudwatch_event, mock_context)
            
            assert response['statusCode'] == 503
            assert response['body']['success'] is False
            assert 'Network unreachable' in response['body']['error']


class TestChunkedProcessing:
    """Tests for chunked processing functionality."""
    
    @pytest.mark.parametrize("chunked_handler,scraper_class,config_attr", [
        (bond_chunked_handler, 'handlers.bond_issuance_handler.BondIssuanceScraper', 'TECH_COMPANY_CIKS'),
        (bdc_chunked_handler, 'handlers.bdc_discount_handler.BDCDiscountScraper', 'BDC_CONFIG'),
        (credit_chunked_handler, 'handlers.credit_fund_handler.CreditFundScraper', 'CREDIT_FUND_CIKS'),
        (bank_chunked_handler, 'handlers.bank_provision_handler.BankProvisionScraper', 'BANK_CIKS'),
    ])
    def test_chunked_processing_logic(self, chunked_handler, scraper_class, config_attr, mock_context):
        """Test chunked processing logic for all handlers."""
        with patch(scraper_class) as mock_scraper_class:
            # Setup mock scraper with config
            mock_scraper = Mock()
            test_config = {'item1': {}, 'item2': {}, 'item3': {}, 'item4': {}}
            setattr(mock_scraper, config_attr, test_config)
            
            mock_result = Mock()
            mock_result.success = True
            mock_result.data = {'value': 1000}
            mock_scraper.execute.return_value = mock_result
            mock_scraper_class.return_value = mock_scraper
            
            # Test first chunk
            chunked_event = {
                'chunk_size': 2,
                'chunk_index': 0
            }
            
            response = chunked_handler(chunked_event, mock_context)
            
            # Assertions
            assert response['statusCode'] == 200
            assert response['body']['success'] is True
            assert response['body']['chunk_index'] == 0
            assert response['body']['has_more_chunks'] is True
            assert response['body']['next_chunk_index'] == 1
            
            # Verify scraper config was modified for chunk
            current_config = getattr(mock_scraper, config_attr)
            assert len(current_config) == 2  # Should only have 2 items for this chunk


class TestLocalExecution:
    """Tests for local execution capabilities."""
    
    def test_bond_handler_local_execution(self):
        """Test that bond handler can be executed locally."""
        # This test verifies the __main__ block works
        import handlers.bond_issuance_handler as bond_module
        
        # Check that MockContext is defined
        assert hasattr(bond_module, 'MockContext')
        
        # Verify MockContext has required methods
        mock_ctx = bond_module.MockContext()
        assert hasattr(mock_ctx, 'aws_request_id')
        assert hasattr(mock_ctx, 'get_remaining_time_in_millis')
        assert callable(mock_ctx.get_remaining_time_in_millis)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])