import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.narrative_generator import MAX_SUMMARY_LENGTH, NarrativeGenerator


class TestNarrativeGenerator(unittest.TestCase):

    @patch('src.services.narrative_generator.GEMINI_API_KEY', 'test_api_key')
    @patch('src.services.narrative_generator.genai')
    def test_init_with_api_key(self, mock_genai):
        generator = NarrativeGenerator()
        mock_genai.configure.assert_called_once_with(api_key='test_api_key')
        self.assertIsNotNone(generator.model)

    @patch('src.services.narrative_generator.GEMINI_API_KEY', None)
    def test_init_without_api_key(self):
        with self.assertRaises(ValueError):
            NarrativeGenerator()

    @patch('src.services.narrative_generator.GEMINI_API_KEY', 'test_api_key')
    @patch('src.services.narrative_generator.genai.GenerativeModel')
    def test_generate_narrative(self, mock_model):
        mock_response = MagicMock()
        mock_response.text = "Narrative"
        mock_model.return_value.generate_content.return_value = mock_response

        generator = NarrativeGenerator()
        narrative = generator.generate_narrative({})

        self.assertEqual(narrative, "Narrative")

    @patch('src.services.narrative_generator.GEMINI_API_KEY', 'test_api_key')
    @patch('src.services.narrative_generator.genai.GenerativeModel')
    def test_generate_narrative_error(self, mock_model):
        mock_model.return_value.generate_content.side_effect = Exception("API Error")

        generator = NarrativeGenerator()
        narrative = generator.generate_narrative({})

        self.assertEqual(narrative, "Error generating narrative.")

    @patch('src.services.narrative_generator.GEMINI_API_KEY', 'test_api_key')
    @patch('src.services.narrative_generator.genai.GenerativeModel')
    def test_generate_recruiter_summary(self, mock_model):
        mock_response = MagicMock()
        mock_response.text = "Summary"
        mock_model.return_value.generate_content_async = AsyncMock(return_value=mock_response)

        generator = NarrativeGenerator()

        async def run_test():
            summary = await generator.generate_recruiter_summary({})
            self.assertEqual(summary, "Summary")

        asyncio.run(run_test())

    @patch('src.services.narrative_generator.GEMINI_API_KEY', 'test_api_key')
    @patch('src.services.narrative_generator.genai.GenerativeModel')
    def test_generate_recruiter_summary_error(self, mock_model):
        mock_model.return_value.generate_content_async.side_effect = Exception("API Error")

        generator = NarrativeGenerator()

        async def run_test():
            summary = await generator.generate_recruiter_summary({})
            self.assertEqual(summary, "Error generating recruiter summary.")

        asyncio.run(run_test())

    @patch('src.services.narrative_generator.GEMINI_API_KEY', 'test_api_key')
    @patch('src.services.narrative_generator.genai.GenerativeModel')
    def test_generate_recruiter_summary_length(self, mock_model):
        long_text = "a" * (MAX_SUMMARY_LENGTH + 100)
        mock_response = MagicMock()
        mock_response.text = long_text
        mock_model.return_value.generate_content_async = AsyncMock(return_value=mock_response)

        generator = NarrativeGenerator()

        async def run_test():
            summary = await generator.generate_recruiter_summary({})
            self.assertLessEqual(len(summary), MAX_SUMMARY_LENGTH)
            self.assertTrue(summary.endswith("..."))

        asyncio.run(run_test())
