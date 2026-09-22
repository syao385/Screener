import unittest
from sources.news_pulse import news_pulse
from sources.catalyst_detector import catalyst_detector
from sources.setup_scorer import SetupScorer
from sources.thesis_lake import thesis_lake

class TestCatalystSentimentEngine(unittest.TestCase):
    def test_multi_source_authority_hierarchy(self):
        """Verify authority ratings: SEC (100) vs PR (85) vs WSJ (75) vs Social (25)."""
        sec_sig = news_pulse.compute_signal_score(80, 80, 'SEC_EDGAR', 0.5)
        pr_sig = news_pulse.compute_signal_score(80, 80, 'PRESS_RELEASE', 0.5)
        wsj_sig = news_pulse.compute_signal_score(80, 80, 'WSJ', 0.5)
        soc_sig = news_pulse.compute_signal_score(80, 80, 'SOCIAL_MEDIA', 0.5)
        
        self.assertEqual(sec_sig['authority'], 100.0)
        self.assertEqual(pr_sig['authority'], 85.0)
        self.assertEqual(wsj_sig['authority'], 75.0)
        self.assertEqual(soc_sig['authority'], 25.0)
        self.assertGreater(sec_sig['composite_score'], wsj_sig['composite_score'])
        self.assertGreater(wsj_sig['composite_score'], soc_sig['composite_score'])

    def test_composite_catalyst_scoring(self):
        """Verify blended institutional catalyst rating calculation."""
        res = news_pulse.compute_composite_catalyst_score(
            pattern_stars=5.0,
            source='SEC_EDGAR',
            sentiment_score=0.8,
            relevance=90.0,
            novelty=85.0
        )
        self.assertGreaterEqual(res['blended_score'], 4.0)
        self.assertLessEqual(res['blended_score'], 5.0)
        self.assertEqual(res['authority'], 100.0)

    def test_sentiment_delta_and_divergence(self):
        """Test Stealth Accumulation and Climax Distribution divergence regimes."""
        stealth = news_pulse.evaluate_divergence_and_sentiment_delta(
            symbol='TEST_STEALTH',
            current_sentiment=0.85,
            prior_sentiment=0.40,
            price_change_pct=-0.5
        )
        self.assertEqual(stealth['regime'], 'STEALTH_ACCUMULATION')
        self.assertIn('Stealth', stealth['label'])

        climax = news_pulse.evaluate_divergence_and_sentiment_delta(
            symbol='TEST_CLIMAX',
            current_sentiment=0.20,
            prior_sentiment=0.60,
            price_change_pct=3.5,
            social_sentiment=0.90,
            social_volume_surge=True
        )
        self.assertEqual(climax['regime'], 'CLIMAX_DISTRIBUTION')
        self.assertIn('Climax', climax['label'])

    def test_setup_scorer_blended_catalyst(self):
        """Test that setup scorer integrates blended catalyst rating."""
        score_res = SetupScorer.calculate_score(
            catalyst_stars=5.0,
            rvol=2.5,
            gap_pct=5.0,
            price=150.0,
            yesterday_high=145.0,
            premarket_high=148.0,
            gamma_skew='Bullish',
            call_wall='160.0',
            pc_ratio=0.55,
            macro_regime='Risk-On',
            pattern_info={'archetype': 'ARCHETYPE_B', 'primary_pattern': 'EP_DAY_1', 'criteria_checklist': {'has_catalyst': True, 'is_above_vwap': True, 'close_location_pct': 85.0}},
            sentiment_score=0.9,
            signal_score=92.0,
            source_authority=100.0
        )
        self.assertGreaterEqual(score_res['score'], 4.0)
        bd = score_res['score_breakdown']
        self.assertIn('blended_catalyst_rating', bd)
        self.assertGreaterEqual(bd['blended_catalyst_rating'], 4.0)

    def test_thesis_lake_sentiment_snapshots(self):
        """Test recording and retrieving daily sentiment snapshots in DuckDB."""
        ok = thesis_lake.record_sentiment_snapshot({
            'symbol': 'NVDA',
            'composite_sentiment': 0.82,
            'sec_sentiment': 0.95,
            'media_sentiment': 0.80,
            'social_sentiment': 0.65,
            'delta_sentiment_7d': 0.35,
            'divergence_regime': 'PEAD_MOMENTUM_ALIGNMENT',
            'price_change_7d': 4.5
        })
        self.assertTrue(ok)
        trend = thesis_lake.get_sentiment_trend('NVDA', days=5)
        self.assertGreaterEqual(len(trend), 1)
        self.assertEqual(trend[0]['symbol'], 'NVDA')
        self.assertEqual(trend[0]['divergence_regime'], 'PEAD_MOMENTUM_ALIGNMENT')

    def test_earnings_catalyst_classification_and_cross_validation(self):
        """Test post-earnings reaction headlines and earnings calendar cross-validation (e.g. SIG)."""
        # 1. Test Barron's post-earnings reaction headline
        hl = "Signet Jewelers Stock Is Having Its Best Day in Over a Year After Earnings"
        scored = catalyst_detector._classify_headline("SIG", hl, "https://barrons.com/...", company_name="Signet Jewelers Ltd")
        self.assertIn(scored[0], ("Earnings Beat & Raise", "Earnings Release"))
        self.assertGreaterEqual(scored[1], 4.5)
        self.assertTrue(scored[4])

        # 2. Test detect_catalyst with earnings_date
        res = catalyst_detector.detect_catalyst("SIG", "Signet Jewelers Ltd", earnings_date="Sep 09 b")
        self.assertIn(res[0], ("Earnings Beat & Raise", "Earnings Release"))
        self.assertEqual(res[1], 5.0)
        self.assertTrue(res[4])

        # 3. Test rich output driver and source type
        rich = catalyst_detector.detect_catalyst_rich("SIG", "Signet Jewelers Ltd", earnings_date="Sep 09 b")
        self.assertEqual(rich["driver_type"], "PRIMARY_DRIVER")
        self.assertEqual(rich["source_type"], "PRESS_RELEASE")
        self.assertEqual(rich["stars"], 5.0)

if __name__ == '__main__':
    unittest.main()
