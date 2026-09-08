from decimal import Decimal
import unittest

from rep import Rep, Mode, RepType
from runner import matches_answer
from workout_template import WorkoutTemplate


class PercentageTests(unittest.TestCase):
    def make(self, kind, value, rate):
        from percentage_rep import PercentageRep
        return PercentageRep(kind, value, rate)

    def test_formulas(self):
        for kind, value, rate, expected in (
            ('of', 240, 15, '36'), ('increase', 80, '12.5', '90'),
            ('decrease', 160, 25, '120'), ('ratio', 30, 120, '25'),
            ('reverse_decrease', 240, 20, '300'),
            ('reverse_increase', 240, 20, '200')):
            with self.subTest(kind=kind):
                self.assertEqual(self.make(kind, value, rate).answer(), Decimal(expected))

    def test_rounding_is_half_up_and_checks_at_stated_precision(self):
        rep = self.make('of', 85, 17)
        self.assertTrue(matches_answer(rep, '14.45'))
        self.assertTrue(matches_answer(rep, '14.450'))
        self.assertFalse(matches_answer(rep, '14.44'))
        third = self.make('ratio', 1, 3)
        self.assertEqual(third.answer(), Decimal('33.33'))
        self.assertIn('two decimal places', third.instruction)
        self.assertTrue(matches_answer(third, '33.3333%'))
        self.assertFalse(matches_answer(third, '33.34'))
        self.assertEqual(self.make('of', 1, '12.5').answer(), Decimal('0.13'))

    def test_input_accepts_decimal_comma_and_percent_only_for_ratio(self):
        self.assertTrue(matches_answer(self.make('of', 85, 17), '14,45'))
        self.assertTrue(matches_answer(self.make('ratio', 30, 120), '25 %'))
        for value in ('NaN', 'Infinity', '1e2', '', '1,234.5', '25%'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.make('of', 100, 25).parse_answer(value)
        self.assertFalse(matches_answer(Rep('10 + 2'), '12.0'))

    def test_templates_opt_in_without_changing_legacy_mixed(self):
        self.assertEqual(WorkoutTemplate.parse('s-p-5').rep_types(), {'p'})
        self.assertEqual(WorkoutTemplate.parse('m-*,p-10').rep_types(), {'a', 's', 'm', 'd', 'p'})
        self.assertEqual(WorkoutTemplate.parse('m-*-10').rep_types(), {'a', 's', 'm', 'd'})

    def test_generated_questions_have_manageable_positive_answers(self):
        for mode in Mode.all():
            for _ in range(150):
                rep = Rep.generate(mode, 'p')
                self.assertGreater(rep.answer(), 0)
                self.assertLessEqual(rep.answer(), 2000)
                self.assertTrue(matches_answer(rep, str(rep.answer())))
                if mode == Mode.SIMPLE:
                    self.assertEqual(rep.answer(), int(rep.answer()))
                    self.assertFalse(rep.kind.startswith('reverse'))
                if mode == Mode.MEDIUM:
                    self.assertFalse(rep.kind.startswith('reverse'))
